import email_handling

def read_email_account():
    # a. fetch unread emails using OAuth2 authentication
    emails = email_handling.fetch_unread_emails("davidplayground333@gmail.com", "wbqq qntg rxys fwid")
    # b. retrieve email metadata
    metadata = [{"subject": email["subject"], "sender": email["from"]} for email in emails]
    # b. retrieve email content
    content = [email["body"] for email in emails]
    # c. retrieve email attachments
    attachments = [email.get("attachments", []) for email in emails]
    return metadata, content, attachments

def move_used_email_to_archive():
    # move used email to archive
    # a. move email to archive folder
    # b. mark email as read
    pass

def save_raw_data_to_chromadb(data):
    # save converted data to chromadb in a raw data collection.
    move_used_email_to_archive()
    pass

def normaliaze_and_clean_data(data): 
    # normalize and clean data
    # remove duplicates
    # remove empty data
    # remove non-text data
    # keep only English and Hebrew text
    # remove non-relevant data
    pass

def extract_text(data):
    # extract data from email
    metadata, content, attachments = data
    extracted_data = {
        "text": [],
        "attachments": [],
        "links": [],
        "images": [],
        "tables": [],
        "code": [],
        "audio": [],
        "video": [],
        "other": []
    }
    
    # a. extract text from email
    for email_content in content:
        if email_content:
            extracted_data["text"].append(email_content)
    
    # b. extract attachments from email
    for email_attachments in attachments:
        extracted_data["attachments"].extend(email_attachments)
    
    # c. extract links from email
    import re
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    for email_content in content:
        if email_content:
            links = re.findall(url_pattern, email_content)
            extracted_data["links"].extend(links)
    
    # d-i. extract other content types based on attachments
    for email_attachments in attachments:
        for attachment in email_attachments:
            if "content_type" in attachment:
                content_type = attachment["content_type"].lower()
                if "image" in content_type:
                    extracted_data["images"].append(attachment)
                elif "audio" in content_type:
                    extracted_data["audio"].append(attachment)
                elif "video" in content_type:
                    extracted_data["video"].append(attachment)
                elif content_type in ["text/html", "text/csv"]:
                    # Simple heuristic for tables (HTML or CSV)
                    extracted_data["tables"].append(attachment)
                elif content_type in ["text/plain", "application/json", "text/x-python"]:
                    # Simple heuristic for code
                    extracted_data["code"].append(attachment)
                else:
                    extracted_data["other"].append(attachment)
    
    return extracted_data

def convert_to_text(data):
    # supported files: doc,ppt,xls,pdf,images,txt
    plainText = extract_text(data)
    print("plainText", plainText)

    # save converted data to chromadb in a raw data collection.
    clean_data = normaliaze_and_clean_data(data)
    save_raw_data_to_chromadb(clean_data)
    pass

def embed_new_data(data):
    # embed raw data
    # save embedded data to chromadb in a processed data collection.
    # metadata: timestamp,sender,subject,vendor
    pass

def enrich_and_index():     
    # enrich new index with metadata
    # save enriched data to chromadb in a processed data collection.
    # metadata such as: Vendor,Type(update,fix,valnerability,news,event,deal,sale,info,other),Product,etc.
    pass
    
def log_new_email():
    # log the new email processed in sqlite.
    pass

if __name__ == "__main__":
    data = read_email_account()
    print("data", data)
    raw_data = convert_to_text(data)
    # embed_new_data(raw_data)
    # enrich_and_index()    