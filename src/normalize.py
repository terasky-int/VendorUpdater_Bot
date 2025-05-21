import os
import email
import logging
import textract

from email import policy
from email.parser import BytesParser


def clean_email(raw_path, config):
    with open(raw_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)

    subject = msg['subject'] or ""
    body_text = ""
    attachments_text = []

    # Extract body text
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get_content_disposition())
            charset = part.get_content_charset()

            # Handle unknown or broken encodings
            if charset and charset.lower() == 'iso-8859-8-i':
                charset = 'iso-8859-8'

            if content_type == "text/plain" and disposition != "attachment":
                try:
                    text = part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True)
                    text = payload.decode(charset or 'utf-8', errors='ignore') if payload else ''
                body_text += text.strip() + "\n"
            elif part.get_filename():
                text = extract_attachment_text(part, config)
                if text:
                    attachments_text.append(text)
    else:
        try:
            body_text = msg.get_content().strip()
        except Exception:
            payload = msg.get_payload(decode=True)
            body_text = payload.decode('utf-8', errors='ignore') if payload else ''

    full_text = subject + "\n" + body_text + "\n" + "\n".join(attachments_text)

    output_dir = os.path.join("data", "clean_text")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, os.path.basename(raw_path).replace(".eml", ".txt"))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    logging.info(f"Cleaned email and saved text to {output_path}")
    return full_text


def extract_attachment_text(part, config):
    filename = part.get_filename()
    if not filename:
        return None

    attachment_data = part.get_payload(decode=True)
    temp_path = os.path.join("/tmp", filename)

    with open(temp_path, "wb") as f:
        f.write(attachment_data)

    try:
        text = textract.process(temp_path).decode("utf-8", errors="ignore")
        os.remove(temp_path)
        return text
    except Exception as e:
        logging.warning(f"Failed to extract attachment {filename}: {e}")
        return None