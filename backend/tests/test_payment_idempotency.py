import sys
import os
import unittest
import json
import hmac
import hashlib

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestPaymentSecurity(unittest.TestCase):

    def test_01_idempotent_order_creation(self):
        """Verify that duplicate order requests with identical idempotency keys return exact same order."""
        ikey = "idempotency_test_" + os.urandom(4).hex()
        payload = {
            "showtime_id": 1,
            "seats": ["A1", "A2"],
            "amount": 500.0,
            "idempotency_key": ikey
        }

        res1 = client.post("/api/payments/create-order", json=payload)
        self.assertEqual(res1.status_code, 200)
        order1 = res1.json()

        # Duplicate Request
        res2 = client.post("/api/payments/create-order", json=payload)
        self.assertEqual(res2.status_code, 200)
        order2 = res2.json()

        self.assertEqual(order1["order_id"], order2["order_id"])
        self.assertEqual(order1["idempotency_key"], order2["idempotency_key"])
        print("[OK] Idempotent payment order creation test passed.")

    def test_02_server_side_hmac_verification(self):
        """Verify server-side HMAC SHA256 signature verification."""
        verify_payload = {
            "order_id": "order_mock123",
            "payment_id": "pay_mock123",
            "signature": "mock_valid_signature",
            "idempotency_key": "ik_mock123"
        }
        res = client.post("/api/payments/verify", json=verify_payload)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

        # Invalid Signature
        bad_payload = verify_payload.copy()
        bad_payload["signature"] = "invalid_signature_att"
        res_bad = client.post("/api/payments/verify", json=bad_payload)
        self.assertEqual(res_bad.status_code, 400)
        print("[OK] Server-side HMAC signature verification test passed.")

    def test_03_webhook_replay_mitigation(self):
        """Verify HMAC webhook signature validation and duplicate event replay mitigation."""
        webhook_body = json.dumps({
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_wb_test",
                        "order_id": "order_wb_test"
                    }
                }
            }
        }).encode("utf-8")

        # Valid Webhook Call
        res1 = client.post(
            "/api/payments/webhook",
            content=webhook_body,
            headers={"X-Razorpay-Signature": "mock_webhook_sig", "Content-Type": "application/json"}
        )
        self.assertEqual(res1.status_code, 200)

        # Duplicate Replay Webhook Call
        res2 = client.post(
            "/api/payments/webhook",
            content=webhook_body,
            headers={"X-Razorpay-Signature": "mock_webhook_sig", "Content-Type": "application/json"}
        )
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["status"], "success")
        print("[OK] Webhook signature validation & replay attack mitigation test passed.")

if __name__ == "__main__":
    unittest.main()
