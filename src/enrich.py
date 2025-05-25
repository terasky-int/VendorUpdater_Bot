import os
import logging
import langdetect
from datetime import datetime
import tldextract
import re

def extract_metadata(clean_text, original_email, config):
    # Fallback values
    subject = original_email.get("subject", "")
    sender = original_email.get("from", "")
    date = original_email.get("date", None)
    vendor = infer_vendor(sender)

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

def infer_vendor(sender_email):
    # Extract actual email from display string
    match = re.search(r"<(.+?)>", sender_email)
    if match:
        sender_email = match.group(1)

    # Use tldextract for domain parsing
    import tldextract
    ext = tldextract.extract(sender_email)
    domain = ext.domain
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
