#!/usr/bin/env python3

"""
Test script for human-in-the-middle debugging functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.human_debug import wait_for_user_input

def test_human_debug():
    """Test the human debugging interface"""
    
    # Test data
    email_id = "test-email-123"
    
    # Test Step 1: Raw email processing
    input_data = {"email_path": "/path/to/email.eml"}
    output_data = {"email_id": email_id, "raw_path": "data/raw_emails/test-email-123.eml"}
    
    print("Testing human-in-the-middle debugging...")
    print("This will show you how the debugging interface works.")
    
    result = wait_for_user_input(
        step_name="1_save_raw_email",
        input_data=input_data,
        output_data=output_data,
        email_id=email_id
    )
    
    if result:
        print("✅ User chose to continue")
    else:
        print("❌ User chose to skip")
        return
    
    # Test Step 2: Classification
    input_data = {"text": "This is a sample email about HashiCorp Vault security updates..."}
    output_data = {
        "vendor": "hashicorp",
        "product": ["vault"],
        "type": ["security", "update"],
        "confidence": 0.85
    }
    
    result = wait_for_user_input(
        step_name="4_classify_content",
        input_data=input_data,
        output_data=output_data,
        email_id=email_id
    )
    
    if result:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test stopped by user")

if __name__ == "__main__":
    test_human_debug()