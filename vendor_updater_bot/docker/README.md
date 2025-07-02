# Docker Deployments

This folder contains Docker configurations for different components of the VendorUpdater Bot.

## ⚠️ Important: Configuration Usage

**Both containers use the global project configuration (`config/config.yaml`) which includes:**
- AWS Bedrock model specifications and regions
- ChromaDB connection settings
- Neo4j database parameters  
- Email processing configurations
- RAG model settings

**Environment variables can override config values at runtime.**

## Structure

```
Docker/
├── rag-api/          # Standalone RAG API container
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env
│   ├── requirements-rag.txt
│   └── README.md
├── ingestion/        # Email ingestion pipeline container
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env
│   └── README.md
└── README.md         # This file
```

## Quick Start

### RAG API (for QA team)
```bash
cd rag-api/
# Edit .env with your remote database IPs
docker-compose up -d
```

### Ingestion Pipeline
```bash
cd ingestion/
# Edit .env with your database configuration
docker-compose up -d
```

## Build Commands

Each subfolder can be built independently:

```bash
# RAG API
cd rag-api/
docker build -f Dockerfile -t rag-api ../..

# Ingestion Pipeline  
cd ingestion/
docker build -f Dockerfile -t ingestion-pipeline ../..
```

## Notes

- Each container has its own configuration and environment files
- Build context is set to the project root (../..) to access all source files
- **Containers use global config/config.yaml for default settings**
- Environment variables override config values at runtime
- RAG API connects to remote databases
- Ingestion pipeline can use local or remote databases

## Production Status

- ✅ RAG API: Production ready, deployed for QA testing
- ✅ Ingestion Pipeline: Ready for deployment
- ✅ Remote Database Support: ChromaDB and Neo4j connections working
- ✅ Expiration Date Filtering: Implemented and tested