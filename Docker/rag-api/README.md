# RAG API Docker Deployment

Standalone RAG API container that connects to remote ChromaDB and Neo4j instances.

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
   curl http://localhost:8000/health
   ```

## Build Only
```bash
docker build -t rag-api .
```

## API Endpoints

- `GET /health` - Health check
- `GET /metadata` - Get available metadata values  
- `POST /query` - Query the RAG system

## Example Query

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me recent security updates from hashicorp",
    "metadata_filters": {"vendor": "hashicorp", "type": "security"},
    "top_k": 5,
    "include_expired": false
  }'
```