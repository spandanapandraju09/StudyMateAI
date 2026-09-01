import sys
import os
import unittest
import concurrent.futures

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestSeatConcurrency(unittest.TestCase):

    def test_01_millisecond_concurrent_seat_race_condition(self):
        """Simulate 10 simultaneous threads attempting to reserve the exact same seat within milliseconds."""
        target_seat = ["B10"]
        showtime_id = 1
        num_threads = 10

        def send_reserve_request(user_idx):
            payload = {
                "showtime_id": showtime_id,
                "seats": target_seat,
                "user_id": 1
            }
            return client.post("/api/bookings/reserve-seats", json=payload)

        # Launch 10 concurrent requests simultaneously using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(send_reserve_request, i) for i in range(num_threads)]
            results = [f.result() for f in futures]

        success_count = sum(1 for r in results if r.status_code == 200)
        conflict_count = sum(1 for r in results if r.status_code == 409)

        # EXACTLY ONE request must succeed; all others MUST be rejected with HTTP 409 Conflict
        self.assertEqual(success_count, 1)
        self.assertEqual(conflict_count, num_threads - 1)
        print(f"[OK] Millisecond Concurrency Race Condition Test Passed: {success_count} succeeded, {conflict_count} rejected with 409 Conflict.")

if __name__ == "__main__":
    unittest.main()
