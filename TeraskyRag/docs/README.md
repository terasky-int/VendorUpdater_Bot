# TeraskyRag Documentation

This directory contains comprehensive documentation for the TeraskyRag system.

## Available Documentation

- `api_spec.json` - Complete OpenAPI specification for all endpoints
- API reference and usage examples available in the main README

## Key Features Documented

### API Endpoints
- **RAG Queries**: `/query` - Natural language search with LLM-generated answers
- **Metadata**: `/metadata` - Available filter values
- **Graph Queries**: `/graph/*` - Vendor-product relationship queries
- **Unified Search**: `/search/unified` - Combined vector and graph search
- **Debug Tools**: `/debug/*` - System inspection and troubleshooting

### Search Capabilities
- Vector similarity search using ChromaDB
- Graph database queries using Neo4j
- Natural language query processing
- Expiration date filtering for time-sensitive content
- Metadata filtering by vendor, product, type, and date

### Configuration
- Remote database connections (ChromaDB, Neo4j)
- AWS Bedrock integration for embeddings and LLM
- Flexible deployment options (local, Docker, cloud)

## Getting Started

1. Review the main README.md for setup instructions
2. Check the API specification in `api_spec.json`
3. Test the system with the provided examples
4. Explore the various search endpoints

## Integration

TeraskyRag works with data processed by the vendor_updater_bot system:
- Reads vector embeddings from ChromaDB
- Queries relationship data from Neo4j
- Provides intelligent search and analysis capabilities