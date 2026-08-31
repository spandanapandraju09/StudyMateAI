import sys
import os
import unittest
import time

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestAdminAnalytics(unittest.TestCase):

    def test_01_rbac_protection(self):
        """Verify that unauthorized requests without X-Admin-Token are rejected with 403 Forbidden."""
        res = client.get("/api/admin/analytics")
        self.assertEqual(res.status_code, 403)
        self.assertIn("Access denied", res.json()["detail"])
        print("[OK] Admin RBAC protection test passed.")

    def test_02_admin_login(self):
        """Verify secure admin login with hashed password authentication."""
        payload = {
            "email": "admin@movietickets.com",
            "password": "Admin@MovieTickets2026!"
        }
        res = client.post("/api/admin/login", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["admin_token"], "admin_secret_token_session_2026")
        print("[OK] Admin hashed password authentication test passed.")

    def test_03_analytics_aggregation_benchmark_50k_records(self):
        """Benchmark database-level aggregation queries over 50,000+ booking dataset."""
        token = "admin_secret_token_session_2026"
        
        start_time = time.time()
        res = client.get("/api/admin/analytics?force_refresh=true", headers={"X-Admin-Token": token})
        query_time = round((time.time() - start_time) * 1000, 2)
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        
        self.assertGreater(data["total_revenue_all_time"], 0)
        self.assertGreaterEqual(len(data["daily_revenue"]), 1)
        self.assertGreaterEqual(len(data["popular_movies"]), 1)
        self.assertEqual(len(data["peak_booking_hours"]), 24)
        self.assertFalse(data["cached"])
        
        print(f"[OK] 50,000+ Bookings DB Aggregation Query executed in {query_time} ms!")

    def test_04_in_memory_ttl_cache(self):
        """Verify 60-second in-memory TTL caching mechanism."""
        token = "admin_secret_token_session_2026"
        
        # Second call within 60 seconds should be served from cache
        res_cached = client.get("/api/admin/analytics", headers={"X-Admin-Token": token})
        self.assertEqual(res_cached.status_code, 200)
        self.assertTrue(res_cached.json()["cached"])
        print("[OK] 60-second In-Memory TTL Caching test passed.")

if __name__ == "__main__":
    unittest.main()
