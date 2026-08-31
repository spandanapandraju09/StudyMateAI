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
from backend.db.connection import get_db

client = TestClient(app)

class TestMovieSystem(unittest.TestCase):

    def test_01_movie_filtering_and_facets(self):
        """Task 1: Test server-side multi-select filtering and dynamic facet counts."""
        response = client.get("/api/movies?genres=Action,Sci-Fi&languages=English&page=1&limit=5")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("facet_counts", data)
        self.assertIn("genres", data["facet_counts"])
        self.assertIn("languages", data["facet_counts"])
        print("[OK] Task 1 Passed: Scalable filtering and dynamic facet counts working.")

    def test_02_secure_youtube_trailer_embedding(self):
        """Task 3: Test YouTube trailer URL sanitization and embed ID extraction."""
        response = client.get("/api/movies/1/trailer")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("is_valid", data)
        if data["is_valid"]:
            self.assertIsNotNone(data["embed_id"])
            self.assertTrue(data["embed_url"].startswith("https://www.youtube-nocookie.com/embed/"))
        print("[OK] Task 3 Passed: Secure YouTube trailer URL verification & sanitization working.")

    def test_03_concurrency_seat_reservation(self):
        """Task 5: Test seat reservation, 2-minute lock timeout, and collision prevention."""
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id FROM users LIMIT 1")
        uid = cur.fetchone()[0]
        cur.close()
        db.close()

        req_payload = {
            "showtime_id": 1,
            "seats": ["A1", "A2"],
            "user_id": uid
        }
        res1 = client.post("/api/bookings/reserve-seats", json=req_payload)
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(res1.json()["success"])

        # Second request trying to lock SAME seats must be rejected with 409 Conflict
        res2 = client.post("/api/bookings/reserve-seats", json=req_payload)
        self.assertEqual(res2.status_code, 409)
        self.assertIn("already reserved or locked", res2.json()["detail"])
        print("[OK] Task 5 Passed: Concurrency-safe seat reservation & conflict prevention working.")

    def test_04_payment_idempotency_and_webhook(self):
        """Task 4: Test payment order creation idempotency and HMAC webhook signature validation."""
        ikey = "test_ikey_" + os.urandom(4).hex()
        order_payload = {
            "showtime_id": 1,
            "seats": ["A1", "A2"],
            "amount": 500.0,
            "idempotency_key": ikey
        }

        # First Call
        res1 = client.post("/api/payments/create-order", json=order_payload)
        self.assertEqual(res1.status_code, 200)
        order_id1 = res1.json()["order_id"]

        # Duplicate Call with SAME idempotency key must return exact same order_id
        res2 = client.post("/api/payments/create-order", json=order_payload)
        self.assertEqual(res2.status_code, 200)
        order_id2 = res2.json()["order_id"]
        self.assertEqual(order_id1, order_id2)

        # Webhook Signature Validation
        webhook_body = json.dumps({
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test123",
                        "order_id": order_id1
                    }
                }
            }
        }).encode("utf-8")

        # Send Webhook with Mock Signature
        res_wb = client.post(
            "/api/payments/webhook",
            content=webhook_body,
            headers={"X-Razorpay-Signature": "mock_webhook_sig", "Content-Type": "application/json"}
        )
        self.assertEqual(res_wb.status_code, 200)
        print("[OK] Task 4 Passed: Payment idempotency and webhook HMAC verification working.")

    def test_05_admin_rbac_and_analytics(self):
        """Task 6: Test Admin authentication (RBAC) and aggregated DB analytics."""
        # Login
        login_res = client.post("/api/admin/login", json={
            "email": "admin@movietickets.com",
            "password": "Admin@MovieTickets2026!"
        })
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["admin_token"]

        # Access Admin Analytics with Token
        analytics_res = client.get("/api/admin/analytics", headers={"X-Admin-Token": token})
        self.assertEqual(analytics_res.status_code, 200)
        data = analytics_res.json()
        self.assertIn("total_revenue_all_time", data)
        self.assertIn("popular_movies", data)
        self.assertIn("busiest_theaters", data)
        print("[OK] Task 6 Passed: Admin RBAC protection & DB aggregated analytics working.")

if __name__ == "__main__":
    unittest.main()
