# VendorUpdater_Bot Complete Pipeline

## System Overview

The VendorUpdater_Bot is a comprehensive system for processing vendor emails, extracting valuable information, and making it searchable through both vector and graph-based approaches. The system consists of two main components:

1. **Email Processing Pipeline**: Runs as a cron job to ingest, process, and store vendor emails
2. **Query API**: Provides endpoints for external agents to query the processed data

## 1. Email Processing Pipeline

### 1.1 Email Harvesting
- **Source**: IMAP server or local .eml files
- **Process**: Fetches unread emails or reads from local directory
- **Output**: Raw email files stored in `data/raw_emails/`

### 1.2 Email Normalization
- **Input**: Raw email files
- **Process**: Cleans HTML, removes signatures, extracts text from attachments
- **Output**: Clean text files stored in `data/clean_text/`

### 1.3 Metadata Extraction & Enrichment
- **Input**: Clean text and email metadata
- **Process**: Extracts sender, date, language; infers vendor from domain
- **Output**: Enriched data structure with metadata

### 1.4 Content Classification
- **Input**: Enriched data
- **Process**: Uses AWS Bedrock (Claude) to classify email type and identify products
- **Output**: Classified data with vendor, product, and type labels

### 1.5 Text Chunking
- **Input**: Classified text
- **Process**: Splits text into manageable chunks for embedding
- **Output**: List of text chunks with position information

### 1.6 Embedding Generation
- **Input**: Text chunks
- **Process**: Generates embeddings using AWS Bedrock Titan
- **Output**: Vector embeddings for each chunk

### 1.7 Dual Storage
- **ChromaDB Storage**:
  - Stores text chunks, embeddings, and metadata
  - Enables vector similarity search
  - Supports metadata filtering

- **Neo4j Storage**:
  - Creates nodes for Vendors, Products, and Emails
  - Establishes relationships (FROM, OFFERS, ABOUT)
  - Enables graph-based queries and analytics

### 1.8 Evaluation (Optional)
- **Input**: Processed emails
- **Process**: Runs RAG tests to evaluate retrieval quality
- **Output**: Evaluation metrics stored in `data/eval/`

## 2. Query API

The system provides a REST API for external agents to query the processed data. The main endpoint is:

### 2.1 RAG API (`rag_api.py`)
- **Endpoint**: `/query` (POST)
- **Input**: JSON with query text, optional metadata filters, and top_k parameter
- **Process**: 
  1. Embeds the query text
  2. Performs hybrid search (vector + metadata)
  3. Generates answer using retrieved documents
- **Output**: JSON with answer and source documents

### 2.2 Graph API (`graph_api.py`)
- **Endpoints**:
  - `/vendors` (GET): List all vendors
  - `/products/{vendor}` (GET): Get products for a vendor
  - `/vendors/{product}` (GET): Get vendors for a product
  - `/timeline` (GET): Get email timeline with filters
  - `/query` (POST): Run custom Cypher query

### 2.3 Unified API (Future Enhancement)
- **Endpoint**: `/unified_search` (POST)
- **Process**: Combines vector search and graph relationships
- **Output**: Enhanced results with both content and relationship data

## 3. External AI Agent Integration

An external AI agent running in a separate pod can interact with the system through the API endpoints:

### 3.1 Example Queries
- **"Show all related updates for vendor X in the past 1 month"**:
  - Use `/query` endpoint with:
    ```json
    {
      "query": "updates for vendor X",
      "metadata_filters": {"vendor": "X", "type": "product update"},
      "top_k": 10
    }
    ```

- **"Are there any known vulnerabilities saved under this vendor?"**:
  - Use `/query` endpoint with:
    ```json
    {
      "query": "security vulnerability",
      "metadata_filters": {"vendor": "X", "type": "security"},
      "top_k": 10
    }
    ```

- **"Show all related events for these vendors: X, Y, Z"**:
  - Use `/query` endpoint with:
    ```json
    {
      "query": "events",
      "metadata_filters": {"vendor": ["X", "Y", "Z"], "type": "event"},
      "top_k": 15
    }
    ```

### 3.2 Integration Flow
1. External AI agent formulates a query based on user request
2. Agent sends HTTP request to the appropriate API endpoint
3. VendorUpdater_Bot processes the query and returns results
4. Agent processes the results and presents information to the user

## 4. Monitoring and Maintenance

- **Logging**: All operations are logged to `logs/pipeline.log`
- **Metrics**: Performance metrics are stored in `logs/metrics.jsonl`
- **Alerts**: Critical issues trigger alerts in `logs/alerts.jsonl`
- **Health Checks**: System health can be monitored via the `/health` endpoint

## 5. Deployment Architecture

- **Email Processing Pipeline**: Runs as a cron job in a Kubernetes pod
- **API Server**: Runs as a separate service in a Kubernetes pod
- **Storage**:
  - ChromaDB: Persistent volume for vector data
  - Neo4j: Separate database service
- **External AI Agent**: Separate pod that communicates with the API