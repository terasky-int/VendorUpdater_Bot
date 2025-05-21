app tech stack:
language: python
vector_db: chromaDB
relational_db: sqlite
llms: bedrock Claude
embedding model: bedrock ...
build as a contenerized app.

app description:
this app will listen to an email inbox (provided in config file),
this inbox will include updates from our vendords and buisness partners.
the app will extract all data from the email, ingest it to be ai-accessable, enrich ti and finally index it.

this data should be later available as a datasource for ai-agents to provide information about a specific vendor or product, and will be able to suggest better solutions, more attractive pricings etc.

pipeline:

1. read email account inbox:
    a. fetch unread emails
    b. retrieve email metadata
    b. retrieve email content
    c. retrieve email attachments
2. convert all collected data to plain text (supported files: doc,ppt,xls,pdf,images,txt).
3. save converted data to chromadb in a raw data collection.
4. embed/vectorize the collected data (metadata: timestamp,sender,subject,vendor)
5. index raw data and extract metadata such as: Vendor,Type(update,fix,valnerability,news,event,deal,sale,info,other),Product,etc.
6. move processed email to used folder
7. log the new email processed in sqlite.