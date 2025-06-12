# Unified API for VendorUpdater Bot

This document describes the unified API implementation that consolidates multiple API endpoints into a single API with organized routes.

## Overview

The unified API combines functionality from:
- RAG API (rag_api.py)
- Graph API (graph_api.py)
- Debug API (debug_api.py)
- API Endpoints (src/api_endpoints.py)

## API Structure

The API is organized into the following route groups:

### RAG Routes
- `/rag/query` - Process a RAG query and return an answer with sources
- `/rag/metadata` - Get unique metadata values from the collection

### Graph Routes
- `/graph/vendors` - Get all vendors
- `/graph/products/{vendor}` - Get products for a specific vendor
- `/graph/vendors/{product}` - Get vendors for a specific product
- `/graph/timeline` - Get timeline of emails for a vendor or product
- `/graph/analytics/count/{vendor}` - Count emails from a specific vendor
- `/graph/analytics/recent` - Count recent emails from a vendor
- `/graph/analytics/security` - Find security-related emails
- `/graph/query` - Run a custom Cypher query

### Debug Routes
- `/debug/raw_search` - Perform a raw search without any filtering
- `/debug/collection_info` - Get detailed information about the collection
- `/debug/test_embedding` - Test embedding generation to check dimensions

### Search Routes
- `/search/unified` - Perform a unified search using both vector and graph capabilities
- `/search/nl` - Process a natural language query and return structured results

### System Routes
- `/health` - Check system health

## Usage

To start the unified API:

```bash
python unified_api.py
```

This will start the API server on port 8000. You can access the Swagger UI documentation at:

```
http://localhost:8000/docs
```

## Benefits of Unification

1. **Consistent Interface**: All endpoints follow the same error handling and response format patterns
2. **Organized Routes**: Endpoints are grouped by functionality for easier discovery
3. **Reduced Code Duplication**: Common functionality is shared across endpoints
4. **Simplified Deployment**: Only one API service needs to be deployed and maintained
5. **Comprehensive Documentation**: All endpoints are documented in a single Swagger UI