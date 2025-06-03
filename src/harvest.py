import imaplib
import email
from email.header import decode_header
import os
import uuid
import logging

# Maintain a mapping of message IDs for later marking
msg_id_map = {}

def fetch_unread_emails(config):
    server = config['email']['imap_server']
    user = config['email']['email_address']
    password = config['email']['email_password']
    folder = config['email'].get('folder', 'INBOX')

    mail = imaplib.IMAP4_SSL(server)
    mail.login(user, password)
    mail.select(folder)

    status, messages = mail.search(None, 'UNSEEN')
    email_ids = messages[0].split()
    logging.info(f"Found {len(email_ids)} unread emails")

    emails = []
    for eid in email_ids:
        _, msg_data = mail.fetch(eid, '(RFC822)')
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        emails.append((eid, msg))  # store tuple of id and email object

    mail.logout()
    return emails

def mark_email_as_read(eid, config):
    if not config['email'].get('mark_as_read', True):
        return

    server = config['email']['imap_server']
    user = config['email']['email_address']
    password = config['email']['email_password']  # Fixed key name to match config
    folder = config['email'].get('folder', 'INBOX')

    mail = imaplib.IMAP4_SSL(server)
    mail.login(user, password)
    mail.select(folder)
    mail.store(eid, '+FLAGS', '\\Seen')
    mail.logout()
    logging.info(f"Marked email ID {eid.decode()} as read")

def save_raw_email(email_obj, config):
    msg_id = str(uuid.uuid4())
    folder = os.path.join("data", "raw_emails")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{msg_id}.eml")

    with open(path, "wb") as f:
        f.write(email_obj.as_bytes())

    logging.info(f"Saved raw email to {path}")
    return msg_id, path