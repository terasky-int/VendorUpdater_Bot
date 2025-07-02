# TeraskyRag

## Overview
TeraskyRag is a Retrieval-Augmented Generation (RAG) system for querying and analyzing vendor email data through vector search, graph database queries, and natural language processing.

## Core Features
- Vector similarity search
- Graph database queries
- Unified search combining multiple approaches
- Natural language query processing
- REST API for external integration

## Getting Started

### Prerequisites
- Python 3.11+
- Docker (optional)
- AWS account with Bedrock access
- Neo4j database (optional)
- ChromaDB (shared with vendor_updater_bot)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/TeraskyRag.git
cd TeraskyRag
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

### Running the API

#### Local Mode
```bash
uvicorn api.rag_api:app --host 0.0.0.0 --port 8000
```

#### Docker
```bash
cd docker/rag-api
docker build -t terasky-rag:latest .
docker run -p 8000:8000 terasky-rag:latest
```

## Configuration
Configuration is stored in `config/config-rag.yaml`. Key settings include:

- ChromaDB connection parameters
- Neo4j connection details
- AWS Bedrock settings
- RAG model configuration

## API Endpoints

### Main Endpoints
- `POST /query`: Search with natural language query
- `GET /health`: Check system health
- `GET /metadata`: Get available metadata values

### Graph Endpoints
- `GET /vendors`: List all vendors
- `GET /products/{vendor}`: Get products for a vendor
- `GET /timeline`: Get email timeline

## Testing
Run the basic functionality tests:
```bash
python tests/tools/test_basic_functionality.py
```

## Architecture
The system consists of three main components:
1. **Search Engine**: Vector, hybrid, and unified search capabilities
2. **Graph Database**: Relationship queries and knowledge graph
3. **API Layer**: REST endpoints for external integration

## License
[Specify your license]