import email_handling
import os

CHROMA_DB_PATH = "./chroma_db"

def read_email_account():
    # a. fetch unread emails using OAuth2 authentication
    emails = email_handling.fetch_unread_emails("davidplayground333@gmail.com", "wbqq qntg rxys fwid")
    # b. retrieve email metadata
    metadata = [{"subject": email["subject"], "sender": email["from"], "date": email.get("date", "")} for email in emails]
    # c. retrieve email content
    content = [email["body"] for email in emails]
    # d. retrieve email attachments
    attachments = [email.get("attachments", []) for email in emails]
    return metadata, content, attachments

def move_used_email_to_archive():
    # move used email to archive
    # a. move email to archive folder
    # b. mark email as read
    pass

def save_raw_data_to_chromadb(data):
    # save converted data to chromadb in a raw data collection.
    import chromadb
    import uuid
    import json
    from datetime import datetime
    
    # Initialize ChromaDB client
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    # Get or create collection for raw data
    collection = client.get_or_create_collection(name="raw_email_data")
    
    # Generate unique ID for this data entry
    doc_id = str(uuid.uuid4())
    
    # Extract email metadata
    email_metadata = data.get("metadata", [])
    if email_metadata and len(email_metadata) > 0:
        # Use the first email's metadata as the base metadata
        base_metadata = {
            "sender": email_metadata[0].get("sender", ""),
            "subject": email_metadata[0].get("subject", ""),
            "date": email_metadata[0].get("date", ""),
            "processed_at": datetime.now().isoformat()
        }
    else:
        base_metadata = {"processed_at": datetime.now().isoformat()}
    
    # Store text content with email metadata
    if data["text"]:
        collection.add(
            documents=data["text"],
            metadatas=[{**base_metadata, "type": "text"} for _ in data["text"]],
            ids=[f"{doc_id}_text_{i}" for i in range(len(data["text"]))]
        )
    
    # Store links as a single document with email metadata
    if data["links"]:
        collection.add(
            documents=[json.dumps(data["links"])],
            metadatas=[{**base_metadata, "type": "links"}],
            ids=[f"{doc_id}_links"]
        )
    
    # Store other data types with email metadata
    for data_type in ["attachments", "images", "tables", "code", "audio", "video", "other"]:
        if data[data_type]:
            collection.add(
                documents=[json.dumps(data[data_type])],
                metadatas=[{**base_metadata, "type": data_type}],
                ids=[f"{doc_id}_{data_type}"]
            )
    
    # move_used_email_to_archive()
    print(f"Data saved to ChromaDB with ID: {doc_id}")
    print(f"Email metadata: {base_metadata}")
    return doc_id

def normaliaze_and_clean_data(data): 
    # normalize and clean data
    import re
    from langdetect import detect, LangDetectException
    
    clean_data = {
        "text": [],
        "attachments": data["attachments"],
        "links": list(set(data["links"])),  # Remove duplicate links
        "images": data["images"],
        "tables": data["tables"],
        "code": data["code"],
        "audio": data["audio"],
        "video": data["video"],
        "other": data["other"],
        "metadata": data.get("metadata", [])  # Preserve metadata
    }
    
    # Process text content
    seen_texts = set()  # For duplicate detection
    for text in data["text"]:
        if not text or not text.strip():
            continue  # Skip empty content
            
        # Basic cleaning
        text = text.strip()
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Skip if duplicate
        if text in seen_texts:
            continue
        seen_texts.add(text)
        
        # Check if text is English or Hebrew
        try:
            lang = detect(text)
            if lang in ['en', 'he', 'iw']:  # 'iw' is an old code for Hebrew
                clean_data["text"].append(text)
        except LangDetectException:
            # If language detection fails, keep the text if it contains Hebrew characters
            if re.search(r'[\u0590-\u05FF]', text):
                clean_data["text"].append(text)
    
    return clean_data

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
        "other": [],
        "metadata": metadata  # Store the email metadata
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

    # save converted data to chromadb in a raw data collection.
    clean_data = normaliaze_and_clean_data(plainText)
    
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
    
    raw_data = convert_to_text(data)
    # embed_new_data(raw_data)
    # enrich_and_index()    