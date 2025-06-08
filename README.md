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
7. Stores in ChromaDB for vector search
8. Provides evaluation tools for RAG performance
9. Offers graph database integration for relationship queries

## Setup

### Prerequisites

- Python 3.10+
- AWS account with Bedrock access
- Docker (optional, for containerized deployment)
- Neo4j (optional, for graph database features)

### Configuration

1. Copy `.env.example` to `.env` and fill in your credentials:
   ```
   EMAIL_PASS=your_email_password
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_neo4j_password
   ```

2. Adjust settings in `config/config.yaml` as needed.

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run with IMAP email fetching
python main.py

# Run with local .eml files
python main.py --local --folder ./path/to/emails
```

## Running as a Container

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build and run manually
docker build -t vendor-updater .
docker run -v ./data:/app/data -v ./logs:/app/logs -v ./config:/app/config --env-file .env vendor-updater
```

## Running as a Cron Job

1. Make the script executable:
   ```bash
   chmod +x cron-job.sh
   ```

2. Add to crontab (runs every 2 hours):
   ```
   0 */2 * * * /path/to/cron-job.sh
   ```

## APIs

### RAG API

Start the RAG API server:
```bash
python rag_api.py
```

Endpoints:
- `GET /health`: Check API health
- `GET /metadata`: Get unique metadata values
- `POST /query`: Query the RAG system

### Graph API

Start the Graph API server:
```bash
python graph_api.py
```

Endpoints:
- `GET /vendors`: List all vendors
- `GET /products/{vendor}`: Get products for a vendor
- `GET /vendors/{product}`: Get vendors for a product
- `GET /timeline`: Get email timeline
- `POST /query`: Run custom Cypher query

## Testing

Run all tests:
```bash
python run_tests.py --all
```

Or run specific tests:
```bash
python run_tests.py --debug  # Run debug search
python run_tests.py --search  # Test search quality
python run_tests.py --api  # Test RAG API
```

## Project Structure

- `src/`: Core modules for the processing pipeline
- `config/`: Configuration files
- `data/`: Data storage (raw emails, clean text, vector DB)
- `logs/`: Application logs
- `misc/`: Miscellaneous files and test data

## Graph Database Integration

The application can integrate with Neo4j to model relationships between vendors, products, and emails:

```bash
# Import all emails to Neo4j
python graph_db.py
```

Example Cypher queries:
```cypher
// Find all security updates for Hashicorp products
MATCH (e:Email)-[:FROM]->(v:Vendor {name: "hashicorp"}),
      (e)-[:ABOUT]->(p:Product)
WHERE e.type CONTAINS "security"
RETURN e.id, e.date, p.name
ORDER BY e.date DESC

// Find related products mentioned in the same emails
MATCH (p1:Product)<-[:ABOUT]-(e:Email)-[:ABOUT]->(p2:Product)
WHERE p1.name < p2.name  // Avoid duplicates
RETURN p1.name, p2.name, COUNT(e) AS email_count
ORDER BY email_count DESC
```