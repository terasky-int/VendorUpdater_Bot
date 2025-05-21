import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup

def fetch_unread_emails(username, password, mailbox="INBOX", max_emails=100):
    # Connect to Gmail's IMAP server
    imap_server = "imap.gmail.com"
    mail = imaplib.IMAP4_SSL(imap_server)
    
    try:
        # Login to your Gmail account
        mail.login(username, password)
        
        # Select mailbox
        mail.select(mailbox)
    except Exception as e:
        print(f"Error logging in: {e}")
        return []

    # Search for UNSEEN (unread) emails
    status, messages = mail.search(None, '(UNSEEN)')
    if status != "OK":
        print("No messages found.")
        return []

    email_ids = messages[0].split()
    result = []

    for i in email_ids[:max_emails]:
        res, msg_data = mail.fetch(i, "(RFC822)")
        if res != "OK":
            continue

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Decode email subject
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            try:
                # Try with the specified encoding
                if encoding:
                    subject = subject.decode(encoding)
                else:
                    subject = subject.decode("utf-8")
            except (LookupError, UnicodeDecodeError):
                # Fallback for Hebrew and other encodings
                try:
                    if encoding == "iso-8859-8-i":
                        subject = subject.decode("iso-8859-8")
                    else:
                        subject = subject.decode("utf-8", errors="ignore")
                except:
                    subject = subject.decode("utf-8", errors="ignore")

        # Get sender information
        from_header = msg.get("From", "")
        
        # Get date information
        date_header = msg.get("Date", "")

        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
                elif content_type == "text/html":
                    html = part.get_payload(decode=True).decode(errors="ignore")
                    soup = BeautifulSoup(html, "html.parser")
                    body = soup.get_text()
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        result.append({
            "subject": subject,
            "body": body.strip(),
            "from": from_header,
            "date": date_header
        })

    mail.logout()
    return result