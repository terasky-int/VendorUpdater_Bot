import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest
from src.normalize import medium_clean

class TestNormalize(unittest.TestCase):
    
    def test_medium_clean_removes_html(self):
        """Test that HTML tags are removed"""
        html_text = "<p>Test paragraph</p><style>body { color: red; }</style>"
        cleaned = medium_clean(html_text)
        self.assertEqual(cleaned, "Test paragraph")
    
    def test_medium_clean_removes_style_blocks(self):
        """Test that style blocks are removed"""
        html_with_style = "Before<style>body { color: red; }</style>After"
        cleaned = medium_clean(html_with_style)
        self.assertEqual(cleaned, "BeforeAfter")
    
    def test_medium_clean_removes_html_comments(self):
        """Test that HTML comments are removed"""
        html_with_comments = "Before<!-- This is a comment -->After"
        cleaned = medium_clean(html_with_comments)
        self.assertEqual(cleaned, "BeforeAfter")
    
    def test_medium_clean_replaces_entities(self):
        """Test that HTML entities are replaced"""
        text_with_entities = "This&nbsp;has&nbsp;spaces"
        cleaned = medium_clean(text_with_entities)
        self.assertEqual(cleaned, "This has spaces")
    
    def test_medium_clean_removes_signatures(self):
        """Test that email signatures are removed"""
        text_with_sig = "Main content\n--\nJohn Doe\nCEO"
        cleaned = medium_clean(text_with_sig)
        self.assertEqual(cleaned, "Main content")
    
    def test_medium_clean_removes_forwarded(self):
        """Test that forwarded blocks are removed"""
        text_with_forward = "Main content\n---------- Forwarded message ----------\nFrom: someone@example.com\nMore content"
        cleaned = medium_clean(text_with_forward)
        self.assertEqual(cleaned, "Main content")
    
    def test_medium_clean_removes_cids(self):
        """Test that CIDs are removed"""
        text_with_cid = "Text with [cid:image001.jpg@01D7F1A2.3B4C5D6E] image"
        cleaned = medium_clean(text_with_cid)
        self.assertEqual(cleaned, "Text with  image")
    
    def test_medium_clean_collapses_newlines(self):
        """Test that multiple newlines are collapsed"""
        text_with_newlines = "Line 1\n\n\n\nLine 2"
        cleaned = medium_clean(text_with_newlines)
        self.assertEqual(cleaned, "Line 1\n\nLine 2")

if __name__ == '__main__':
    unittest.main()