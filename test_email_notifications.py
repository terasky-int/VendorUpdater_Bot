"""
Test script for email notification system
"""
import os
import sys
import time
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from src.email_notifications import send_pipeline_summary_email, create_run_summary
from src import llm_utils

def test_email_notifications():
    """Test the email notification system"""
    
    # Load environment variables
    load_dotenv()
    
    # Load configuration
    config = llm_utils.load_config()
    
    # Create test run summary
    test_email_details = [
        {
            "vendor": "hashicorp",
            "product": "vault",
            "type": "security",
            "subject": "Vault Security Update - Critical Patch Available"
        },
        {
            "vendor": "palo alto",
            "product": "cortex xdr",
            "type": "announcement",
            "subject": "New Cortex XDR Features Released"
        },
        {
            "vendor": "hashicorp", 
            "product": "terraform",
            "type": "webinar",
            "subject": "Terraform Best Practices Webinar - Register Now"
        }
    ]
    
    run_summary = create_run_summary(
        emails_processed=3,
        processing_time=45.67,
        success=True,
        email_details=test_email_details
    )
    
    print("Testing email notification system...")
    print(f"Notifications enabled: {config.get('notifications', {}).get('enabled', False)}")
    
    if not config.get('notifications', {}).get('enabled', False):
        print("⚠️  Email notifications are disabled in config. Enable them to test.")
        print("Set notifications.enabled: true in config/config.yaml")
        return
    
    # Test successful run notification
    print("Sending test notification...")
    success = send_pipeline_summary_email(config, run_summary)
    
    if success:
        print("✅ Test notification sent successfully!")
    else:
        print("❌ Failed to send test notification")
    
    # Wait before sending second email
    print("\nWaiting 3 seconds before sending failure notification...")
    time.sleep(3)
    
    # Test failed run notification
    print("Testing failure notification...")
    failed_summary = create_run_summary(
        emails_processed=1,
        processing_time=12.34,
        success=False,
        error="Database connection failed",
        email_details=test_email_details[:1]
    )
    
    success = send_pipeline_summary_email(config, failed_summary)
    
    if success:
        print("✅ Test failure notification sent successfully!")
    else:
        print("❌ Failed to send test failure notification")

if __name__ == "__main__":
    test_email_notifications()