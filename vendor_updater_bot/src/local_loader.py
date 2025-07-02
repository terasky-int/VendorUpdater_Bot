import os
import uuid
from email import policy
from email.parser import BytesParser

def load_local_emails(folder_path):
    eml_files = [f for f in os.listdir(folder_path) if f.endswith(".eml")]
    emails = []

    for filename in eml_files:
        path = os.path.join(folder_path, filename)
        with open(path, "rb") as f:
            msg = BytesParser(policy=policy.default).parse(f)  # <- actual EmailMessage
            email_id = msg.get("Subject", str(uuid.uuid4()))  # fallback to UUID if missing
            emails.append((email_id, msg))

    return emails
