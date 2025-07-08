# Repository Separation Guide

This guide explains how to extract the two standalone projects from this repository.

## Overview

The VendorUpdater_Bot repository has been split into two independent projects:

1. **vendor_updater_bot** - Email ingestion and processing system
2. **TeraskyRag** - RAG (Retrieval-Augmented Generation) query system

## Extraction Steps

### 1. Extract vendor_updater_bot

```bash
# Create new directory
mkdir vendor_updater_bot_standalone
cd vendor_updater_bot_standalone

# Copy the vendor_updater_bot subfolder contents
cp -r /path/to/VendorUpdater_Bot/vendor_updater_bot/* .

# Initialize git repository
git init
git add .
git commit -m "Initial commit: Vendor Updater Bot standalone"
```

### 2. Extract TeraskyRag

```bash
# Create new directory
mkdir TeraskyRag_standalone
cd TeraskyRag_standalone

# Copy the TeraskyRag subfolder contents
cp -r /path/to/VendorUpdater_Bot/TeraskyRag/* .

# Initialize git repository
git init
git add .
git commit -m "Initial commit: TeraskyRag standalone"
```

## Project Dependencies

### vendor_updater_bot
- **Purpose**: Email ingestion and processing
- **Dependencies**: ChromaDB (write), AWS Bedrock, IMAP servers
- **Output**: Processed emails stored in ChromaDB

### TeraskyRag
- **Purpose**: Intelligent querying and search
- **Dependencies**: ChromaDB (read), Neo4j (optional), AWS Bedrock
- **Input**: Processed emails from ChromaDB

## Shared Resources

Both projects can share:
- **ChromaDB instance**: vendor_updater_bot writes, TeraskyRag reads
- **Neo4j database**: Optional for TeraskyRag graph features
- **AWS Bedrock**: Used by both for embeddings and LLM operations

## Configuration

Each project has its own configuration:
- `vendor_updater_bot/config/config.yaml` - Ingestion settings
- `TeraskyRag/config/config-rag.yaml` - RAG and search settings

## Environment Variables

### vendor_updater_bot
```bash
EMAIL_PASS=your_email_password
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
NOTIFICATION_EMAIL=notifications@company.com
CHROMA_HOST=your_chromadb_host
```

### TeraskyRag
```bash
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
NEO4J_URI=bolt://your_neo4j_host:7687
NEO4J_PASSWORD=your_neo4j_password
CHROMA_HOST=your_chromadb_host
```

## Deployment Architecture

```
[Email Sources] → [vendor_updater_bot] → [ChromaDB] → [TeraskyRag] → [Users/APIs]
                                      ↘ [Neo4j] ↗
```

## Testing Each Project

### vendor_updater_bot
```bash
cd vendor_updater_bot_standalone
python test_config.py
python tests/tools/test_basic_functionality.py
python main.py --local --folder misc/tst_emls
```

### TeraskyRag
```bash
cd TeraskyRag_standalone
python test_config.py
python tests/tools/test_basic_functionality.py
uvicorn api.rag_api:app --host 0.0.0.0 --port 8000
```

## Docker Deployment

Each project includes Docker configurations:

### vendor_updater_bot
```bash
cd vendor_updater_bot_standalone/docker
docker-compose up -d
```

### TeraskyRag
```bash
cd TeraskyRag_standalone/docker/rag-api
docker-compose up -d
```

## Integration

The projects integrate through shared data stores:

1. **vendor_updater_bot** processes emails and stores in ChromaDB
2. **TeraskyRag** reads from ChromaDB to provide search capabilities
3. Both can optionally use Neo4j for graph relationships

## Next Steps

After extraction:

1. **Set up CI/CD** for each project independently
2. **Configure monitoring** for both systems
3. **Set up shared infrastructure** (ChromaDB, Neo4j)
4. **Test end-to-end workflow** from ingestion to querying
5. **Update documentation** with deployment-specific details

## Support

Each project now has its own comprehensive README with setup and usage instructions.