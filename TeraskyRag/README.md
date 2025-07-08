# TeraskyRag

A Retrieval-Augmented Generation (RAG) system for querying and analyzing vendor email data through vector search, graph database queries, and natural language processing.

## Overview

TeraskyRag provides intelligent search capabilities over processed vendor emails using:
- **Vector Search**: Semantic similarity search using ChromaDB and AWS Bedrock embeddings
- **Graph Database**: Relationship queries using Neo4j for vendor-product connections
- **Unified Search**: Combined vector and graph search for enhanced results
- **Natural Language Processing**: Conversational query interface
- **REST API**: Complete API for external integration

## Features

- ✅ Vector similarity search with metadata filtering
- ✅ Graph database queries for relationship exploration
- ✅ Unified search combining multiple approaches
- ✅ Natural language query processing
- ✅ Expiration date filtering for time-sensitive content
- ✅ REST API with comprehensive endpoints
- ✅ Docker deployment support
- ✅ Real-time health monitoring

## Quick Start

### Prerequisites

- Python 3.11+
- AWS account with Bedrock access
- ChromaDB instance (local or remote)
- Neo4j database (optional, for graph features)

### Installation

1. **Clone and setup:**
```bash
git clone <repository-url>
cd TeraskyRag
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Update configuration:**
```bash
# Edit config/config-rag.yaml with your settings
```

### Running the API

#### Local Development
```bash
# Start the main RAG API
uvicorn api.rag_api:app --host 0.0.0.0 --port 8000

# Or start the unified API (all endpoints)
uvicorn api.unified_api:app --host 0.0.0.0 --port 8000
```

#### Docker Deployment
```bash
cd docker/rag-api
docker-compose up -d
```

## API Endpoints

### Core RAG Endpoints
- `POST /query` - Search with natural language query and get LLM-generated answers
- `GET /metadata` - Get available metadata values for filtering
- `GET /health` - System health check

### Graph Database Endpoints
- `GET /graph/vendors` - List all vendors
- `GET /graph/products/{vendor}` - Get products for a vendor
- `GET /graph/timeline` - Get email timeline with filters
- `POST /graph/query` - Execute custom Cypher queries

### Advanced Search Endpoints
- `POST /search/unified` - Unified search combining vector and graph
- `POST /search/nl` - Natural language query processing

### Debug Endpoints
- `GET /debug/raw_search` - Raw search without filtering
- `GET /debug/collection_info` - ChromaDB collection information

## Example Usage

### Basic Query
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest security updates from HashiCorp?",
    "metadata_filters": {"vendor": "hashicorp", "type": "security"},
    "top_k": 5
  }'
```

### Natural Language Query
```bash
curl -X POST "http://localhost:8000/search/nl" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me recent webinars from Palo Alto about Prisma"}'
```

## Configuration

Key configuration sections in `config/config-rag.yaml`:

```yaml
vector_store:
  use_remote: true
  remote_host: "your-chromadb-host"
  remote_port: 8000
  collection_name: "vendor_emails"

neo4j:
  uri: bolt://your-neo4j-host:7687
  user: neo4j
  password: ${NEO4J_PASSWORD}

bedrock:
  region: eu-west-1
  embedding_model: amazon.titan-embed-text-v2:0
  classification_model: anthropic.claude-3-haiku-20240307-v1:0

rag:
  answer_model: "anthropic.claude-3-sonnet-20240229-v1:0"
  max_tokens: 700
  temperature: 0.0
```

## Testing

Run basic functionality tests:
```bash
python tests/tools/test_basic_functionality.py
```

Test configuration loading:
```bash
python test_config.py
```

Test Docker build:
```bash
python test_docker.py
```

## Architecture

TeraskyRag consists of three main layers:

1. **API Layer** (`api/`): REST endpoints for external access
2. **Search Engine** (`src/`): Vector, hybrid, and unified search implementations
3. **Graph Database** (`graph/`): Neo4j integration for relationship queries

## Data Sources

TeraskyRag queries data that has been processed by the vendor_updater_bot ingestion system:
- **ChromaDB**: Stores text chunks with vector embeddings and metadata
- **Neo4j**: Stores relationships between vendors, products, and emails

## Deployment

### Docker Production Deployment
```bash
cd docker/rag-api
# Edit docker-compose.yml with your environment
docker-compose up -d
```

### Health Monitoring
The system provides comprehensive health checks:
- ChromaDB connectivity and document counts
- Neo4j database status
- AWS Bedrock service availability

## API Documentation

Complete API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI spec: `docs/api_spec.json`

## License

[Specify your license]

## Support

For issues and questions, please refer to the documentation in the `docs/` directory or create an issue in the repository.