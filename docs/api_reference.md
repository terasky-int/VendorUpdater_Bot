# RAG API Reference - Docker Deployment

This document provides the API reference for the Docker-deployed RAG API for QA testing.

## Overview

The RAG API provides vector-based search capabilities using ChromaDB with AWS Bedrock for answer generation. It includes expiration date filtering to prevent outdated content from appearing in search results.

## Docker Deployment

**Base URL**: `http://localhost:8001`

**Container**: `rag_api:v0.1` running on port 8001

**No Authentication Required** (for QA testing)

## Key Features

- ✅ Vector search with ChromaDB
- ✅ AWS Bedrock answer generation  
- ✅ Expiration date filtering
- ✅ Metadata filtering (vendor, product, type)
- ✅ Remote database connections

## API Endpoints

### 1. Query Emails with RAG

Performs vector search with LLM-generated answers and expiration filtering.

**Endpoint**: `POST /query`

**Request Body**:
```json
{
  "query": "What are the latest updates from hashicorp?",
  "metadata_filters": {
    "vendor": "hashicorp",
    "type": "security"
  },
  "top_k": 5,
  "include_expired": false
}
```

**Parameters**:
- `query` (string, required): The search query text
- `metadata_filters` (object, optional): Filters to apply
  - `vendor` (string): Filter by vendor name
  - `product` (string): Filter by product name  
  - `type` (string): Filter by email type
- `top_k` (integer, optional): Number of results (default: 5)
- `include_expired` (boolean, optional): Include expired events (default: false)

**Response**:
```json
{
  "answer": "According to the email, HashiCorp is making the following changes to their product offerings and purchasing models starting March 8, 2025...",
  "sources": [
    {
      "text": "What's Changing? Starting March 8, 2025, all HCP customers will purchase through one of the following models...",
      "metadata": {
        "vendor": "hashicorp",
        "product": "hcp, vault, terraform, boundary, packer",
        "type": "announcement, update",
        "date": "2025-04-04T08:30:49",
        "email_id": "e604ff31-9038-4c5b-b383-caf80a91e142",
        "chunk_index": 6
      }
    }
  ]
}
```

### 2. Get Available Metadata

Returns all available metadata values for filtering.

**Endpoint**: `GET /metadata`

**Response**:
```json
{
  "vendors": ["google", "portworx", "hashicorp"],
  "products": [
    "hcp, vault, terraform, boundary, packer",
    "Portworx Enterprise",
    "Gemini 2.5, Gemma 3"
  ],
  "types": [
    "announcement, update",
    "event, webinar",
    "announcement, event, update, webinar"
  ],
  "sample_metadata": [
    {
      "vendor": "portworx",
      "product": "Portworx Enterprise", 
      "type": "event, webinar",
      "date": "2024-05-29T13:06:24",
      "email_id": "1d963cf7-ec7f-4dd6-83a2-1870e9e6bb4a",
      "chunk_index": 0
    }
  ],
  "total_documents": 18
}
```

### 3. Health Check

Checks API health and database connections.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "document_count": 18,
  "sample_document": {
    "metadata_keys": ["product", "email_id", "chunk_index", "type", "vendor", "date"],
    "document_preview": "Another Portworx 101: Hands-on Labs is coming right up!\nHi there,\n\nWe missed having you at our last "
  }
}
```

## Test Commands for QA

### Basic Health Check
```bash
curl http://localhost:8001/health
```

### Get Available Data
```bash
curl http://localhost:8001/metadata
```

### Test Query (bypasses LLM)
```bash
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "top_k": 3}'
```

### Real Query with LLM
```bash
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest updates from hashicorp?",
    "metadata_filters": {"vendor": "hashicorp"},
    "top_k": 5,
    "include_expired": false
  }'
```

### Test Expiration Filtering
```bash
# This should exclude expired June 2024 Portworx events
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "portworx hands-on labs",
    "metadata_filters": {"vendor": "portworx"},
    "include_expired": false
  }'
```

### Include Expired Content
```bash
# This should include expired events
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "portworx hands-on labs", 
    "metadata_filters": {"vendor": "portworx"},
    "include_expired": true
  }'
```

## QA Testing Scenarios

### 1. Basic Functionality
- ✅ Health check returns 200 OK
- ✅ Metadata endpoint shows available vendors/products
- ✅ Test query bypasses LLM and returns documents

### 2. Search Quality
- ✅ Vendor filtering works (hashicorp, portworx, google)
- ✅ Product filtering works
- ✅ Type filtering works (event, webinar, announcement)

### 3. Expiration Date Filtering
- ✅ `include_expired: false` excludes past events (default)
- ✅ `include_expired: true` includes past events
- ✅ June 2024 Portworx events are filtered by default

### 4. LLM Answer Generation
- ✅ Real queries generate comprehensive answers
- ✅ Sources are provided with metadata
- ✅ AWS Bedrock integration working

### 5. Error Handling
- ✅ Invalid JSON returns 422 error
- ✅ Empty results handled gracefully
- ✅ AWS Bedrock errors handled gracefully

## Current Data in System

**Total Documents**: 18 chunks from processed emails

**Available Vendors**:
- `hashicorp` - HCP, Vault, Terraform updates
- `portworx` - Portworx Enterprise events  
- `google` - Gemini, Gemma announcements

**Sample Queries for Testing**:
- "What are the latest updates from hashicorp?"
- "Show me portworx events"
- "Tell me about google cloud announcements"
- "Find security updates"
- "Show me webinar invitations"

## Notes for QA Team

- **No authentication required** for testing
- **Port 8001** (not 8000 - that's ChromaDB)
- **Expiration filtering is automatic** unless explicitly disabled
- **LLM responses may vary** but should be coherent and relevant
- **Test both expired and non-expired content** scenarios