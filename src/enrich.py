import os
import logging
import langdetect
from datetime import datetime
import tldextract
import re
from collections import Counter

def extract_metadata(clean_text, original_email, config):
    # Fallback values
    subject = original_email.get("subject", "")
    sender = original_email.get("from", "")
    date = original_email.get("date", None)
    vendor = infer_vendor(sender, original_email)

    # Detect language
    try:
        language = langdetect.detect(clean_text)
    except:
        language = "unknown"

    # Format date
    try:
        parsed_date = datetime.strptime(date[:25], "%a, %d %b %Y %H:%M:%S")
        received_at = parsed_date.isoformat()
    except Exception:
        received_at = datetime.now().isoformat()

    metadata = {
        "subject": subject,
        "sender": sender,
        "received_at": received_at,
        "vendor": vendor,
        "language": language,
        "text": clean_text
    }

    logging.info(f"Extracted metadata for sender {sender}, vendor {vendor}, language {language}")
    return metadata

def extract_original_sender(email_data):
    """Extract original sender from forwarded email."""
    # Check for "From:" in the email body (common in forwarded emails)
    if "body" in email_data and isinstance(email_data.get("body", ""), str):
        # Look for patterns like "From: someone@vendor.com"
        from_match = re.search(r"From:.*?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", 
                              email_data.get("body", ""), re.IGNORECASE)
        if from_match:
            return from_match.group(1)
    
    # Check for original sender in headers
    headers = email_data.get("headers", {})
    if headers:
        for header in ["X-Forwarded-For", "Original-From", "Reply-To"]:
            if header in headers:
                return headers[header]
    
    return None

def extract_vendor_from_content(email_data):
    """Extract vendor name from email content using various heuristics."""
    body = email_data.get("body", "")
    subject = email_data.get("subject", "")
    
    # Common vendor names to look for
    vendors = ["dell", "microsoft", "aws", "google", "ibm", "vmware", "cisco", "oracle", "hashicorp"]
    
    # Check subject for vendor names
    for vendor in vendors:
        if vendor in subject.lower():
            return vendor
    
    # Check for vendor names in the body
    for vendor in vendors:
        if vendor in body.lower():
            return vendor
            
    # Look for domain names in URLs that might indicate vendor
    url_pattern = r'https?://(?:www\.)?([a-zA-Z0-9-]+)\.[a-zA-Z0-9-.]+'
    urls = re.findall(url_pattern, body)
    if urls:
        # Return the most common domain that's not your company
        domains = [domain for domain in urls if domain.lower() != "terasky"]
        if domains:
            most_common = Counter(domains).most_common(1)[0][0]
            return most_common.lower()
    
    return None

def infer_vendor(sender_email, original_email=None):
    # Extract actual email from display string
    match = re.search(r"<(.+?)>", sender_email)
    if match:
        sender_email = match.group(1)

    # Use tldextract for domain parsing
    ext = tldextract.extract(sender_email)
    domain = ext.domain
    
    # If sender is from your company, try to find the original sender
    if domain.lower() == "terasky":
        # 1. Check for original sender in headers
        if original_email:
            # Look for original sender in headers
            original_sender = extract_original_sender(original_email)
            if original_sender:
                return infer_vendor(original_sender)
                
            # 2. Look for vendor mentions in content
            content_vendor = extract_vendor_from_content(original_email)
            if content_vendor:
                return content_vendor
    
    return domain.lower() if domain else "unknown"



if __name__ == "__main__":
    test_senders = [
        "davidg@terasky.com",                       # ✅ terasky
        "no-reply@reply.hashicorp.com",            # ✅ hashicorp
        "support@ibm.com",                         # ✅ ibm
        "updates@marketing.vmware.co.uk",          # ✅ vmware
        "alerts@security.microsoft.io",            # ✅ microsoft
        "noreply@info.google.net",                 # ✅ google
        "random@email"                             # ❌ unknown
    ]

    for email in test_senders:
        vendor = infer_vendor(email)
        print(f"{email:40s} => {vendor}")
