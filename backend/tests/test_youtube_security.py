import sys
import os
import unittest

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.routers.movie_router import extract_youtube_id

class TestYouTubeTrailerSecurity(unittest.TestCase):

    def test_01_valid_youtube_urls(self):
        """Test extraction of valid 11-character YouTube video IDs."""
        valid_urls = [
            ("https://www.youtube.com/watch?v=YoHD9XEInc0", "YoHD9XEInc0"),
            ("https://youtu.be/zSWdZVtXT7E", "zSWdZVtXT7E"),
            ("https://www.youtube.com/embed/EXeTwQWrcwY", "EXeTwQWrcwY"),
            ("https://www.youtube.com/watch?v=YoHD9XEInc0&feature=shared", "YoHD9XEInc0")
        ]
        for url, expected_id in valid_urls:
            extracted = extract_youtube_id(url)
            self.assertEqual(extracted, expected_id)
        print("[OK] Valid YouTube URL extraction test passed.")

    def test_02_xss_and_malicious_script_rejection(self):
        """Test XSS script injection and malicious URL rejection."""
        malicious_inputs = [
            "https://www.youtube.com/watch?v=<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "https://malicious-site.com/watch?v=YoHD9XEInc0",
            "https://www.youtube.com/watch?v=12345' OR '1'='1",
            "https://www.youtube.com/watch?v=short"  # Invalid length
        ]
        for input_url in malicious_inputs:
            extracted = extract_youtube_id(input_url)
            self.assertNotEqual(extracted, "<script>alert('XSS')</script>")
            # Ensure extracted is either None or strictly 11-char safe string
            if extracted:
                self.assertEqual(len(extracted), 11)
                self.assertTrue(extracted.isalnum() or '_' in extracted or '-' in extracted)
        print("[OK] XSS script injection & malicious URL rejection test passed.")

if __name__ == "__main__":
    unittest.main()
