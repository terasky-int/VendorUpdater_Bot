import os
import logging
import langdetect
from datetime import datetime


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
        received_at = datetime.utcnow().isoformat()

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
    if "@" in sender_email:
        domain = sender_email.split("@")[-1]
        return domain.split(".")[0].lower()
    return "unknown"
