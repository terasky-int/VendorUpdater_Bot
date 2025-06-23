# Vendor Email Updater Bot

A containerized application that periodically checks for new vendor email updates, processes them, and makes them available for RAG (Retrieval-Augmented Generation) applications.

## Overview

This application:
1. Harvests emails from an IMAP server or local .eml files
2. Cleans and normalizes email content
3. Extracts metadata and enriches content
4. Classifies emails by vendor, product, and type using AWS Bedrock
5. Chunks text for embedding
6. Generates embeddings using AWS Bedrock
7. Stores in ChromaDB for vector search and Neo4j for graph relationships
8. Provides evaluation tools for RAG performance

## Project Structure

```
VendorUpdater_Bot/
├── src/                  # Core application code
├── config/               # Configuration files
├── data/                 # Data storage
├── logs/                 # Log files
├── Tests/                # Test scripts and utilities
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── tools/            # Test utilities
├── ui/                   # UI components
│   └── streamlit/        # Streamlit UI
├── docs/                 # Documentation
└── misc/                 # Miscellaneous files
    └── tst_emls/         # Test email files
```

## Setup

### Prerequisites

- Python 3.10+
- AWS account with Bedrock access
- Neo4j (optional, for graph database features)
- Docker (optional, for containerized deployment)

### Configuration

1. Copy `.env.example` to `.env` and fill in your credentials:
   ```
   EMAIL_PASS=your_email_password
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_neo4j_password
   NOTIFICATION_EMAIL=your_notification_email@gmail.com
   NOTIFICATION_EMAIL_PASS=your_notification_email_password
   ```

2. Adjust settings in `config/config.yaml` as needed.

3. Configure email notifications (optional):
   ```yaml
   notifications:
     enabled: true
     smtp_server: smtp.gmail.com
     smtp_port: 587
     sender_email: ${NOTIFICATION_EMAIL}
     sender_password: ${NOTIFICATION_EMAIL_PASS}
     recipients:
       - admin@company.com
   ```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run with IMAP email fetching
python main.py

# Run with local .eml files
python main.py --local --folder ./misc/tst_emls
```

## Application Flow

1. **Email Harvesting**
   - Fetch unread emails from IMAP server or local .eml files
   - Save raw emails to data/raw_emails/ with UUID filenames

2. **Normalization**
   - Parse raw emails and extract text content
   - Clean HTML, remove signatures, boilerplates, etc.
   - Extract text from attachments when possible
   - Save cleaned text to data/clean_text/

3. **Enrichment**
   - Extract metadata (sender, date, language)
   - Infer vendor from email domain

4. **Classification**
   - Use AWS Bedrock (Claude) to classify email type (marketing, security, technical)
   - Identify products mentioned in the email
   - Associate with vendor products from configuration

5. **Chunking**
   - Split text into manageable chunks using RecursiveCharacterTextSplitter
   - Assign chunk IDs and positions for traceability

6. **Embedding**
   - Generate embeddings for each chunk using AWS Bedrock Titan
   - Prepare metadata for each chunk

7. **Indexing**
   - Store chunks, embeddings, and metadata in ChromaDB
   - Record entries in manifest.jsonl for tracking
   - Store relationship data in Neo4j graph database

8. **Evaluation** (optional)
   - Run RAG tests on processed emails
   - Generate evaluation metrics

9. **Notifications** (optional)
   - Send email summary after each pipeline run
   - Include processing statistics and email details
   - Configurable recipients and SMTP settings

## Search and Query Capabilities

### Vector Search (ChromaDB)
1. User submits a query text and optional metadata filters
2. Query text is embedded using AWS Bedrock Titan
3. ChromaDB performs similarity search with metadata filtering
4. Results are ranked by vector similarity
5. Top-k results are returned with their metadata

### Graph Search (Neo4j)
1. User submits a Cypher query or uses predefined analytical queries
2. Neo4j executes the query against the graph database
3. Results show relationships between vendors, products, and emails
4. Analytical queries provide counts, timelines, and relationship insights

### Hybrid Search
1. Combine vector search for semantic understanding with graph search for relationships
2. Use vector search to find relevant content
3. Use graph search to explore connections and metadata
4. Natural language interface translates user queries to appropriate search strategy

## Tools and Utilities

### Testing Tools
```bash
# Run unit tests
python Tests/run_unit_tests.py

# Run comprehensive tests
python Tests/tools/run_tests.py --all

# Test search quality
python Tests/tools/test_search_quality.py

# Test analytical queries
python Tests/tools/test_analytics.py
```

### UI Tools
```bash
# Run Streamlit UI
streamlit run ui/streamlit/inspect_db_ui.py
```

### Graph Database Tools
```bash
# Interactive Cypher query tool
python Tests/tools/cypher_query.py

# Natural language query interface
python Tests/tools/nl_query.py
```

### Monitoring
```bash
# Check system health
python src/monitoring.py
```

## Documentation

- [Graph Database Integration](docs/graph_database.md)

## License

[Your License]