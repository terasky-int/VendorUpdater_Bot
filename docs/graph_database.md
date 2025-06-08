# Graph Database Integration

## Overview
The VendorUpdater_Bot integrates with Neo4j to model relationships between vendors, products, and emails. This allows for complex queries that explore connections between entities and provides analytical capabilities beyond what vector search can offer.

## Setup

### Installation
1. Install Neo4j Desktop or use Neo4j Aura (cloud version)
   - Download Neo4j Desktop: https://neo4j.com/download/
   - Or sign up for Neo4j Aura: https://neo4j.com/cloud/aura/

2. Create a new database with password
   - For Neo4j Desktop: Create a new project, add a local DBMS
   - For Neo4j Aura: Create a new instance

3. Set environment variables:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

### Configuration
No additional configuration is needed beyond the environment variables. The graph database integration will automatically use these settings.

## Data Model

### Nodes
- **Vendor**: Represents email senders
  - Properties: `name` (e.g., "hashicorp", "google")

- **Product**: Represents products mentioned in emails
  - Properties: `name` (e.g., "vault", "terraform")

- **Email**: Represents individual emails
  - Properties: `id`, `date`, `type`

### Relationships
- **FROM**: Connects Email to Vendor
  - `(Email)-[:FROM]->(Vendor)`
  - Indicates which vendor sent the email

- **OFFERS**: Connects Vendor to Product
  - `(Vendor)-[:OFFERS]->(Product)`
  - Indicates which products a vendor offers

- **ABOUT**: Connects Email to Product
  - `(Email)-[:ABOUT]->(Product)`
  - Indicates which products are mentioned in an email

## Usage

### Importing Data
Import emails to Neo4j:
```python
from graph_db import import_all_emails
import_all_emails()
```

### Basic Queries
Get all vendors:
```python
from graph_db import run_graph_query
vendors = run_graph_query("MATCH (v:Vendor) RETURN v.name AS name")
```

Get products for a vendor:
```python
from graph_db import get_vendor_products
products = get_vendor_products("hashicorp")
```

Get emails from a vendor:
```python
from graph_db import get_email_timeline
emails = get_email_timeline("hashicorp")
```

### Analytical Queries
Count emails by vendor:
```python
from graph_db import count_vendor_emails
count = count_vendor_emails("hashicorp")
```

Find recent emails:
```python
from graph_db import count_recent_emails
count = count_recent_emails(vendor_name="google", days=7)
```

Find security-related emails:
```python
from graph_db import find_security_emails
emails = find_security_emails(days=30)
```

### Cypher Query Examples
```cypher
// Count emails by vendor
MATCH (e:Email)-[:FROM]->(v:Vendor)
RETURN v.name AS vendor, count(e) AS email_count
ORDER BY email_count DESC

// Find emails about specific products
MATCH (e:Email)-[:ABOUT]->(p:Product)
WHERE p.name IN ['vault', 'terraform']
RETURN e.id, e.date, e.type, p.name AS product

// Find vendors with the most products
MATCH (v:Vendor)-[:OFFERS]->(p:Product)
WITH v, count(p) AS product_count
RETURN v.name AS vendor, product_count
ORDER BY product_count DESC

// Find related products (products mentioned in the same email)
MATCH (p1:Product)<-[:ABOUT]-(e:Email)-[:ABOUT]->(p2:Product)
WHERE p1.name < p2.name
RETURN p1.name AS product1, p2.name AS product2, count(e) AS email_count
ORDER BY email_count DESC
```

## Tools

### Command-line Tools
- `cypher_query.py`: Interactive Cypher query tool
  ```bash
  python Tests/tools/cypher_query.py
  ```

- `simple_query.py`: Simple script to display all data
  ```bash
  python Tests/tools/simple_query.py
  ```

- `show_all_data.py`: Comprehensive data display
  ```bash
  python Tests/tools/show_all_data.py
  ```

### Natural Language Interface
- `nl_query.py`: Natural language query interface
  ```bash
  python Tests/tools/nl_query.py
  ```

  Example queries:
  - "How many emails from hashicorp vendor?"
  - "How many emails received in the past week from vendor google?"
  - "What vulnerabilities reported in the past month from all vendors?"
  - "What products does hashicorp offer?"

## Integration with Vector Search
The graph database complements the vector search capabilities by providing:

1. **Relationship Exploration**: Find connections between vendors, products, and emails
2. **Analytical Queries**: Count, aggregate, and analyze email patterns
3. **Metadata Filtering**: Filter search results by vendor, product, or type

To combine graph and vector search:
```python
from src.hybrid_search import hybrid_search
from graph_db import get_vendor_products

# Get products for a vendor
products = get_vendor_products("hashicorp")
product_names = [p["product"] for p in products]

# Search for content about those products
for product in product_names:
    results = hybrid_search(product, {"vendor": "hashicorp"}, top_k=3)
    # Process results...
```

## Performance Considerations
- The graph database is optimized for relationship queries, not full-text search
- Use vector search for content-based queries and graph search for relationship queries
- Consider indexing frequently queried properties for better performance
- For large datasets, consider using Neo4j's APOC library for batch operations