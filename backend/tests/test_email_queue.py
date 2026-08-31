import sys
import os
import asyncio
import unittest

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.db.connection import get_db
from backend.services.ticket_email_service import render_ticket_email, process_ticket_email_with_retry

class TestTicketEmailQueue(unittest.TestCase):

    def test_01_template_rendering(self):
        """Verify Jinja2 ticket confirmation HTML template rendering."""
        context = {
            "booking_id": 9999,
            "movie_title": "Galactic Odyssey",
            "language": "English",
            "screen_name": "IMAX Screen 1",
            "theater_name": "PVR Superplex",
            "theater_city": "New York",
            "show_time": "2026-09-01 19:30:00",
            "seats": ["A1", "A2"],
            "total_amount": 500.00,
            "payment_id": "pay_test9999"
        }
        html_out = render_ticket_email(context)
        self.assertIn("TICKET CONFIRMED", html_out)
        self.assertIn("Galactic Odyssey", html_out)
        self.assertIn("PVR Superplex", html_out)
        self.assertIn("A1, A2", html_out)
        print("[OK] Email Template Rendering Test Passed.")

    def test_02_background_retry_queue_logging(self):
        """Verify background task execution, status logging, and delivery record creation."""
        async def run_queue_test():
            email_context = {
                "booking_id": 8888,
                "movie_title": "Inception Prime",
                "language": "English",
                "screen_name": "Screen 2",
                "theater_name": "INOX Cinema",
                "theater_city": "Chicago",
                "show_time": "2026-09-01 21:00:00",
                "seats": ["B5", "B6"],
                "total_amount": 600.00,
                "payment_id": "pay_test8888"
            }
            await process_ticket_email_with_retry(
                booking_id=8888,
                recipient="test_customer@cinemapass.com",
                subject="Ticket Confirmation #8888",
                email_context=email_context,
                max_retries=1
            )

        asyncio.run(run_queue_test())

        # Check DB Log Entry
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT recipient, status, attempts FROM email_delivery_logs WHERE booking_id = 8888")
        row = cur.fetchone()
        cur.close()
        db.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "test_customer@cinemapass.com")
        self.assertIn(row[1], ["delivered", "failed"])
        print("[OK] Background Queue Retry & Log Verification Passed.")

if __name__ == "__main__":
    unittest.main()
