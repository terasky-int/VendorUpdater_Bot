import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest
from unittest.mock import MagicMock
from src.enrich import extract_metadata, infer_vendor

class TestEnrich(unittest.TestCase):
    
    def test_infer_vendor_from_email(self):
        """Test vendor inference from email addresses"""
        test_cases = [
            ("user@hashicorp.com", "hashicorp"),
            ("user@mail.google.com", "google"),
            ("user@aws.amazon.com", "amazon"),
            ("user@unknown-domain.xyz", "unknown-domain"),
            ("Invalid email", "unknown")
        ]
        
        for email, expected in test_cases:
            with self.subTest(email=email):
                result = infer_vendor(email)
                self.assertEqual(result, expected)
    
    def test_infer_vendor_with_display_name(self):
        """Test vendor inference from email with display name"""
        email = "HashiCorp Support <support@hashicorp.com>"
        result = infer_vendor(email)
        self.assertEqual(result, "hashicorp")
    
    def test_extract_metadata_basic(self):
        """Test basic metadata extraction"""
        # Create mock email object
        mock_email = MagicMock()
        mock_email.get.side_effect = lambda key, default=None: {
            "subject": "Test Subject",
            "from": "test@example.com",
            "date": "Mon, 01 Jan 2023 12:00:00 +0000"
        }.get(key, default)
        
        # Test extraction
        clean_text = "This is a test email body"
        config = {}
        result = extract_metadata(clean_text, mock_email, config)
        
        # Verify results
        self.assertEqual(result["subject"], "Test Subject")
        self.assertEqual(result["sender"], "test@example.com")
        self.assertEqual(result["vendor"], "example")
        self.assertEqual(result["text"], clean_text)
        self.assertIn("received_at", result)
        self.assertIn("language", result)

if __name__ == '__main__':
    unittest.main()