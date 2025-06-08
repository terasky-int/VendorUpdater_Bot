"""
Test script for analytical queries
"""

import logging
from graph_db import (
    count_vendor_emails,
    count_recent_emails,
    find_security_emails,
    get_email_timeline
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def test_analytics():
    """Test analytical query functions"""
    
    print("\n=== Testing Analytical Queries ===\n")
    
    # Test vendor email count
    print("1. How many emails exist from the hashicorp vendor?")
    count = count_vendor_emails("hashicorp")
    print(f"   Answer: {count} emails\n")
    
    # Test recent emails count
    print("2. How many emails were received in the past 30 days from all vendors?")
    count = count_recent_emails(days=30)
    print(f"   Answer: {count} emails\n")
    
    # Test recent emails from specific vendor
    print("3. How many emails were received in the past 30 days from Google?")
    count = count_recent_emails("google", days=30)
    print(f"   Answer: {count} emails\n")
    
    # Test security emails
    print("4. What vulnerabilities were reported in the past 30 days from all vendors?")
    emails = find_security_emails(days=30)
    if emails:
        print(f"   Found {len(emails)} security-related emails:")
        for email in emails:
            print(f"   - {email['date']}: {email['vendor']} - {email['product']}")
    else:
        print("   No security-related emails found in the past 30 days")
    print()
    
    # Test email timeline
    print("5. What emails were received from hashicorp?")
    timeline = get_email_timeline("hashicorp")
    if timeline:
        print(f"   Found {len(timeline)} emails:")
        for email in timeline[:3]:  # Show only first 3 for brevity
            print(f"   - {email['date']}: {email['product']} - {email['type']}")
        if len(timeline) > 3:
            print(f"   ... and {len(timeline) - 3} more")
    else:
        print("   No emails found from hashicorp")

if __name__ == "__main__":
    test_analytics()