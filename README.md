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

## Setup

### Prerequisites

- Python 3.10+
- AWS account with Bedrock access
- Docker (optional, for containerized deployment)

### Configuration

1. Copy `.env.example` to `.env` and fill in your credentials:
   ```
   EMAIL_PASS=your_email_password
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
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

## Evaluation Tools

- `inspect_chromadb.py`: View contents of the ChromaDB collection
- `inspect_db_ui.py`: Simple Streamlit UI for exploring the database
- `global_query_eval.py`: Run evaluation queries against the database
- `rag_answers.py`: Generate RAG answers for evaluation queries

## Project Structure

- `src/`: Core modules for the processing pipeline
- `config/`: Configuration files
- `data/`: Data storage (raw emails, clean text, vector DB)
- `logs/`: Application logs
- `misc/`: Miscellaneous files and test data

## License

[Your License]