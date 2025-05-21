def read_email_account():
    # a. fetch unread emails
    # b. retrieve email metadata
    # b. retrieve email content
    # c. retrieve email attachments
    pass

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
    # remove non-english data
    # remove non-relevant data
    pass

def convert_to_text(data):
    # supported files: doc,ppt,xls,pdf,images,txt

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
    raw_data = convert_to_text(data)
    embed_new_data(raw_data)
    enrich_and_index()    
