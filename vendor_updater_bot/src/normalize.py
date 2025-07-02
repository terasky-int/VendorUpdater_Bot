import os
import re
import email
import logging
import textract
from email import policy
from email.parser import BytesParser
from email_reply_parser import EmailReplyParser

# Regex patterns for medium cleanup
FORWARD_RE = re.compile(r'(^|\n)__+ Forwarded message __+[\s\S]+', re.IGNORECASE)
CID_RE = re.compile(r'\[cid:[^\]]+\]')
SIGNATURE_RE = re.compile(
    r'(^|\n)--+\s*\n'  # signature delimiter
    r'[\s\S]+$',       # everything after the delimiter
    re.MULTILINE
)
BOILERPLATE_RE = re.compile(
    r'(©\s*\d{4}|This message was produced and distributed by|CAUTION: This email originated)[\s\S]+$',
    re.IGNORECASE
)
# Strip HTML tags
HTML_TAG_RE = re.compile(r'<[^>]+>')
# Strip HTML comments
HTML_COMMENT_RE = re.compile(r'<!--([\s\S]*?)-->', re.MULTILINE) # Strip <style> blocks
STYLE_TAG_RE = re.compile(r'<style[\s\S]+?</style>', re.IGNORECASE)


def extract_attachment_text(part, config):
    filename = part.get_filename()
    if not filename:
        return None

    attachment_data = part.get_payload(decode=True)
    temp_path = os.path.join('/tmp', filename)

    with open(temp_path, 'wb') as f:
        f.write(attachment_data)

    try:
        tesseract_path = config.get('ocr', {}).get('tesseract_path')
        if tesseract_path:
            os.environ['TESSERACT_PATH'] = tesseract_path
            os.environ['PATH'] = os.pathsep.join([tesseract_path, os.environ.get('PATH', '')])

        text = textract.process(temp_path).decode('utf-8', errors='ignore')
        return text
    except Exception as e:
        logging.warning(f'Failed to extract attachment {filename}: {e}')
        return None
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def medium_clean(text: str) -> str:
    """
    Perform intermediate-level cleanup:
      1. Remove <style> blocks and HTML comments
      2. Replace HTML entities like &nbsp; with spaces
      3. Strip HTML tags
      4. Strip forwarded blocks
      5. Keep only topmost reply via EmailReplyParser
      6. Remove CIDs, signatures, and boilerplate footers
      7. Collapse runs of two or more blank lines into a single blank line
    """
    # 1. Remove <style> blocks and comments
    text = STYLE_TAG_RE.sub('', text)
    text = HTML_COMMENT_RE.sub('', text)

    # 2. Replace non-breaking space entities
    text = text.replace('&nbsp;', ' ')

    # 3. Strip any remaining HTML tags
    text = HTML_TAG_RE.sub('', text)

    # 4. Strip forwarded blocks
    text = FORWARD_RE.sub('', text)

    # 5. Keep only the topmost reply
    text = EmailReplyParser.parse_reply(text) or ''

    # 6. Remove CIDs
    text = CID_RE.sub('', text)

    # 7. Remove signature blocks
    text = SIGNATURE_RE.sub('', text)

    # 8. Remove boilerplate footers/disclaimers
    text = BOILERPLATE_RE.sub('', text)

    # 9. Collapse runs of two or more blank lines into a single blank line
    text = re.sub(r'\n{2,}', '\n\n', text).strip()

    return text


def clean_email(raw_path, config, do_medium_clean=True):
    """
    Read and clean an email from .eml to plain text, with optional medium cleanup.
    """
    # Parse raw .eml
    with open(raw_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)

    subject = msg['subject'] or ''
    body_text = ''
    attachments_text = []

    # Extract text and html parts
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get_content_disposition())
            charset = part.get_content_charset()

            if charset and charset.lower() == 'iso-8859-8-i':
                charset = 'iso-8859-8'

            # Plain-text
            if content_type == 'text/plain' and disposition != 'attachment':
                try:
                    text = part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True)
                    text = payload.decode(charset or 'utf-8', errors='ignore') if payload else ''
                body_text += text.strip() + '\n'
            # HTML fallback
            elif content_type == 'text/html' and disposition != 'attachment':
                html = part.get_content()
                html = STYLE_TAG_RE.sub('', html)
                html = HTML_COMMENT_RE.sub('', html)
                body_text += HTML_TAG_RE.sub('', html).strip() + '\n'
            # Attachments
            elif part.get_filename():
                text = extract_attachment_text(part, config)
                if text:
                    attachments_text.append(text)
    else:
        try:
            content = msg.get_content()
            if msg.get_content_type() == 'text/html':
                content = STYLE_TAG_RE.sub('', content)
                content = HTML_COMMENT_RE.sub('', content)
                body_text = HTML_TAG_RE.sub('', content).strip()
            else:
                body_text = content.strip()
        except Exception:
            payload = msg.get_payload(decode=True)
            body_text = payload.decode('utf-8', errors='ignore') if payload else ''

    full_text = subject + '\n' + body_text + '\n' + '\n'.join(attachments_text)
    cleaned = medium_clean(full_text) if do_medium_clean else full_text

    # Save cleaned text
    output_dir = os.path.join('data', 'clean_text')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, os.path.basename(raw_path).replace('.eml', '.txt'))
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(cleaned)

    logging.info(f'Cleaned email and saved text to {output_path}')
    return cleaned