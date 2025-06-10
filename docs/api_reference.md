# VendorUpdater_Bot API Reference

This document provides a comprehensive reference for all API endpoints available in the VendorUpdater_Bot system.

## Overview

The VendorUpdater_Bot provides several API endpoints for querying and interacting with processed vendor emails. The API is divided into three main components:

1. **RAG API**: Vector-based search using ChromaDB
2. **Graph API**: Relationship-based queries using Neo4j
3. **Unified API**: Combined approach leveraging both vector and graph capabilities

## Base URL

All API endpoints are relative to the base URL of your deployment:

```
http://<host>:<port>/api/v1
```

## Authentication

API requests require authentication using an API key. Include the API key in the request header:

```
Authorization: Bearer <api_key>
```

## RAG API Endpoints

### Search Emails

Performs a vector-based search on email content with optional metadata filtering.

**Endpoint**: `/query`

**Method**: POST

**Request Body**:
```json
{
  "query": "security vulnerability in vault",
  "metadata_filters": {
    "vendor": "hashicorp",
    "type": "security"
  },
  "top_k": 5
}
```

**Parameters**:
- `query` (string, required): The search query text
- `metadata_filters` (object, optional): Filters to apply to the search
  - `vendor` (string or array): Filter by vendor name(s)
  - `product` (string or array): Filter by product name(s)
  - `type` (string or array): Filter by email type(s)
  - `date` (object): Filter by date range with `start` and `end` properties
- `top_k` (integer, optional): Number of results to return (default: 5)

**Response**:
```json
{
  "results": [
    {
      "document": "HashiCorp has released a security update for Vault addressing CVE-2023-1234...",
      "metadata": {
        "vendor": "hashicorp",
        "product": "vault",
        "type": "security",
        "date": "2023-06-15",
        "email_id": "email_123"
      },
      "score": 0.92
    },
    {
      "document": "Critical security patch available for HashiCorp Vault...",
      "metadata": {
        "vendor": "hashicorp",
        "product": "vault",
        "type": "security",
        "date": "2023-05-22",
        "email_id": "email_456"
      },
      "score": 0.87
    }
  ],
  "total_results": 2
}
```

### Get Email by ID

Retrieves a specific email by its ID.

**Endpoint**: `/email/{email_id}`

**Method**: GET

**Parameters**:
- `email_id` (path parameter, required): The ID of the email to retrieve

**Response**:
```json
{
  "email_id": "email_123",
  "subject": "Security Update: HashiCorp Vault CVE-2023-1234",
  "date": "2023-06-15",
  "sender": "security@hashicorp.com",
  "vendor": "hashicorp",
  "products": ["vault"],
  "type": "security",
  "content": "HashiCorp has released a security update for Vault addressing CVE-2023-1234...",
  "attachments": []
}
```

## Graph API Endpoints

### List All Vendors

Returns a list of all vendors in the system.

**Endpoint**: `/vendors`

**Method**: GET

**Response**:
```json
{
  "vendors": [
    {
      "name": "hashicorp",
      "email_count": 42,
      "product_count": 5
    },
    {
      "name": "google",
      "email_count": 37,
      "product_count": 8
    }
  ],
  "total": 15
}
```

### Get Products by Vendor

Returns all products associated with a specific vendor.

**Endpoint**: `/products/{vendor}`

**Method**: GET

**Parameters**:
- `vendor` (path parameter, required): The name of the vendor

**Response**:
```json
{
  "vendor": "hashicorp",
  "products": [
    {
      "name": "vault",
      "email_count": 18
    },
    {
      "name": "terraform",
      "email_count": 15
    },
    {
      "name": "consul",
      "email_count": 7
    }
  ],
  "total": 5
}
```

### Get Vendors by Product

Returns all vendors associated with a specific product.

**Endpoint**: `/vendors/{product}`

**Method**: GET

**Parameters**:
- `product` (path parameter, required): The name of the product

**Response**:
```json
{
  "product": "kubernetes",
  "vendors": [
    {
      "name": "google",
      "email_count": 12
    },
    {
      "name": "hashicorp",
      "email_count": 5
    }
  ],
  "total": 2
}
```

### Get Email Timeline

Returns a timeline of emails with optional filters.

**Endpoint**: `/timeline`

**Method**: GET

**Query Parameters**:
- `vendor` (string, optional): Filter by vendor name
- `product` (string, optional): Filter by product name
- `type` (string, optional): Filter by email type
- `days` (integer, optional): Number of days to look back (default: 30)
- `limit` (integer, optional): Maximum number of results to return (default: 10)

**Response**:
```json
{
  "timeline": [
    {
      "email_id": "email_789",
      "date": "2023-06-20",
      "subject": "Terraform Cloud Migration Webinar",
      "vendor": "hashicorp",
      "product": "terraform",
      "type": "webinar"
    },
    {
      "email_id": "email_456",
      "date": "2023-05-22",
      "subject": "Critical security patch for Vault",
      "vendor": "hashicorp",
      "product": "vault",
      "type": "security"
    }
  ],
  "total": 2
}
```

### Run Custom Cypher Query

Executes a custom Cypher query against the Neo4j database.

**Endpoint**: `/query`

**Method**: POST

**Request Body**:
```json
{
  "query": "MATCH (e:Email)-[:FROM]->(v:Vendor) WHERE v.name = $vendor RETURN e.id AS email_id, e.date AS date, e.type AS type LIMIT 5",
  "parameters": {
    "vendor": "hashicorp"
  }
}
```

**Parameters**:
- `query` (string, required): The Cypher query to execute
- `parameters` (object, optional): Parameters for the Cypher query

**Response**:
```json
{
  "results": [
    {
      "email_id": "email_123",
      "date": "2023-06-15",
      "type": "security"
    },
    {
      "email_id": "email_456",
      "date": "2023-05-22",
      "type": "security"
    }
  ],
  "total": 2
}
```

## Unified API Endpoints

### Unified Search

Performs a combined search using both vector and graph capabilities.

**Endpoint**: `/unified_search`

**Method**: POST

**Request Body**:
```json
{
  "query": "recent security updates from hashicorp",
  "top_k": 5
}
```

**Parameters**:
- `query` (string, required): Natural language query text
- `top_k` (integer, optional): Number of results to return (default: 5)

**Response**:
```json
{
  "results": [
    {
      "document": "HashiCorp has released a security update for Vault addressing CVE-2023-1234...",
      "metadata": {
        "vendor": "hashicorp",
        "product": "vault",
        "type": "security",
        "date": "2023-06-15",
        "email_id": "email_123"
      },
      "score": 0.92
    }
  ],
  "related_entities": {
    "products": [
      {
        "product": "vault",
        "count": 3
      },
      {
        "product": "terraform",
        "count": 1
      }
    ],
    "vendors": [
      {
        "vendor": "hashicorp",
        "count": 4
      }
    ]
  },
  "extracted_parameters": {
    "filters": {
      "vendor": "hashicorp",
      "type": "security"
    },
    "graph_filters": {
      "days": 30
    }
  }
}
```

### Natural Language Query

Processes a natural language query and returns structured results.

**Endpoint**: `/nl_query`

**Method**: POST

**Request Body**:
```json
{
  "query": "How many emails from hashicorp in the past week?"
}
```

**Parameters**:
- `query` (string, required): Natural language query text

**Response**:
```json
{
  "answer": "There are 5 emails from hashicorp in the past week.",
  "query_type": "count",
  "parameters": {
    "vendor": "hashicorp",
    "days": 7
  },
  "data": {
    "count": 5,
    "emails": [
      {
        "email_id": "email_123",
        "date": "2023-06-15",
        "subject": "Security Update: HashiCorp Vault CVE-2023-1234"
      }
    ]
  }
}
```

## Health Check

### API Health Check

Checks the health status of the API and its dependencies.

**Endpoint**: `/health`

**Method**: GET

**Response**:
```json
{
  "status": "healthy",
  "components": {
    "api": "healthy",
    "chromadb": "healthy",
    "neo4j": "healthy"
  },
  "version": "1.0.0"
}
```

## Error Responses

All API endpoints return standard HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response body:
```json
{
  "error": {
    "code": "invalid_parameter",
    "message": "Invalid vendor name provided"
  }
}
```

## Rate Limiting

API requests are rate-limited to 100 requests per minute per API key. Rate limit information is included in the response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1623869430
```

## Pagination

List endpoints support pagination using the following query parameters:

- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Number of items per page (default: 10, max: 100)

Pagination information is included in the response:

```json
{
  "pagination": {
    "total": 42,
    "per_page": 10,
    "current_page": 1,
    "total_pages": 5
  },
  "results": [
    // ...
  ]
}
```