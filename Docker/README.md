# Docker Deployments

This folder contains Docker configurations for different components of the VendorUpdater Bot.

## Structure

```
Docker/
├── rag-api/          # Standalone RAG API container
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env
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
docker build -t rag-api .

# Ingestion Pipeline  
cd ingestion/
docker build -t ingestion-pipeline .
```

## Notes

- Each container has its own configuration and environment files
- Build context is set to the project root (../..) to access all source files
- RAG API connects to remote databases
- Ingestion pipeline can use local or remote databases