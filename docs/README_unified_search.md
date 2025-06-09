# Unified Search Implementation

This document describes the unified search implementation for the VendorUpdater_Bot project, which combines vector search, metadata filtering, and graph relationships.

## Overview

The unified search approach integrates three key components:

1. **Vector Search**: Semantic search using embeddings from AWS Bedrock Titan
2. **Graph Database**: Relationship-based search using Neo4j
3. **Natural Language Processing**: Query understanding and parameter extraction

## Components

### 1. Unified Search API (`Tests/tools/unified_search_api.py`)

The core API module that provides the unified search functionality:

- `process_search_query(query)`: Extracts search parameters from natural language queries
- `unified_search(query_text, filters, graph_filters, top_k)`: Performs the hybrid search
- `get_vendor_products_enhanced(vendor_name)`: Enhanced product lookup by vendor

### 2. Natural Language Interface (`Tests/tools/nl_query_enhanced.py`)

A command-line interface for testing the unified search:

- Processes natural language queries
- Formats and displays search results
- Handles various query types (product listings, email counts, content search)

### 3. Test Module (`Tests/tools/unified_search.py`)

A test implementation with sample queries and mock data:

- Demonstrates the unified search pipeline
- Provides mock data for visualization
- Includes comprehensive error handling

## Usage

### Basic Search

```python
from Tests.tools.unified_search_api import unified_search

# Simple search with query text only
results = unified_search("recent security updates")

# Search with explicit filters
results = unified_search(
    "terraform updates",
    filters={"vendor": "hashicorp", "product": "terraform"},
    graph_filters={"days": 30},
    top_k=5
)
```

### Natural Language Processing

```python
from Tests.tools.unified_search_api import process_search_query

# Extract search parameters from natural language
params = process_search_query("Show me recent security updates from hashicorp")
print(params["filters"])  # {'vendor': 'hashicorp', 'type': 'security'}
print(params["graph_filters"])  # {'days': 30}
```

### Command-line Interface

Run the enhanced natural language query interface:

```
python -m Tests.tools.nl_query_enhanced
```

Example queries:
- "Show me recent security updates"
- "What's new from hashicorp about terraform"
- "List all products from hashicorp"

## Integration

To integrate the unified search into the main application:

1. Copy the `unified_search_api.py` module to the appropriate location
2. Import the functions in your API or UI modules
3. Use the `unified_search` function as the main entry point for search operations

## Future Improvements

- Add more sophisticated NLP for query understanding
- Implement query expansion for better recall
- Add support for faceted search and filtering
- Enhance ranking algorithm with more graph features
- Add caching for frequently accessed results