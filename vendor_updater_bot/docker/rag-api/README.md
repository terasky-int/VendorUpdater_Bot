# RAG API Docker Deployment

Standalone RAG API container that connects to remote ChromaDB and Neo4j instances.

## ⚠️ Important: Configuration

**The Docker build uses the global config file (`config/config.yaml`) which contains:**
- AWS Bedrock models and region settings
- ChromaDB connection details  
- Neo4j connection parameters
- RAG model specifications

**Environment variables override config values at runtime:**
- `AWS_DEFAULT_REGION` overrides `bedrock.region`
- `CHROMA_HOST`/`CHROMA_PORT` override `vector_store.remote_host/remote_port`
- `NEO4J_URI` overrides `neo4j.neo4j_uri`

## Quick Start

1. **Configure environment:**
   ```bash
   # Edit .env with your actual values
   nano .env
   ```

2. **Build and run:**
   ```bash
   docker-compose up -d
   ```

3. **Test:**
   ```bash
   curl http://localhost:8001/health
   ```

## Build Commands

**From this directory:**
```bash
docker build -f Dockerfile -t rag-api ../..
```

**From project root:**
```bash
docker build -f Docker/rag-api/Dockerfile -t rag-api .
```

## API Endpoints

- `GET /health` - Health check
- `GET /metadata` - Get available metadata values  
- `POST /query` - Query the RAG system

## Example Query

```bash
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me recent security updates from hashicorp",
    "metadata_filters": {"vendor": "hashicorp", "type": "security"},
    "top_k": 5,
    "include_expired": false
  }'
```