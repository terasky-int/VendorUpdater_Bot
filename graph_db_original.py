"""
Graph database integration for VendorUpdater_Bot
"""

import logging
import os
from src import llm_utils
from py2neo import Graph, Node, Relationship

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Neo4j connection settings - should be moved to config or env vars
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

def connect_to_graph():
    """Connect to Neo4j database"""
    try:
        graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        logging.info(f"Connected to Neo4j database at: {NEO4J_URI}")
        return graph
    except Exception as e:
        logging.error(f"Failed to connect to Neo4j: {e}")
        return None

def create_schema(graph):
    """Create constraints and indexes for the graph schema"""
    try:
        # Create constraints
        graph.run("CREATE CONSTRAINT vendor_name IF NOT EXISTS FOR (v:Vendor) REQUIRE v.name IS UNIQUE")
        graph.run("CREATE CONSTRAINT product_name IF NOT EXISTS FOR (p:Product) REQUIRE p.name IS UNIQUE")
        graph.run("CREATE CONSTRAINT email_id IF NOT EXISTS FOR (e:Email) REQUIRE e.id IS UNIQUE")
        
        # Create indexes
        graph.run("CREATE INDEX email_date IF NOT EXISTS FOR (e:Email) ON (e.date)")
        graph.run("CREATE INDEX email_type IF NOT EXISTS FOR (e:Email) ON (e.type)")
        
        logging.info("Created Neo4j schema constraints and indexes")
    except Exception as e:
        logging.error(f"Failed to create schema: {e}")

def add_email_to_graph(graph, email_id, metadata):
    """Add email data to the graph database"""
    try:
        # Extract metadata
        vendor = metadata.get("vendor", "unknown")
        product_str = metadata.get("product", "unknown")
        email_type = metadata.get("type", "unknown")
        date = metadata.get("date", "1970-01-01")
        
        # Create vendor node
        vendor_node = Node("Vendor", name=vendor)
        graph.merge(vendor_node, "Vendor", "name")
        
        # Create email node
        email_node = Node("Email", 
                         id=email_id,
                         date=date,
                         type=email_type)
        graph.merge(email_node, "Email", "id")
        
        # Create FROM relationship between email and vendor
        from_rel = Relationship(email_node, "FROM", vendor_node)
        graph.merge(from_rel)
        
        # Handle multiple products
        if isinstance(product_str, list):
            # If product is already a list
            products = product_str
        elif isinstance(product_str, str):
            # If product is a comma-separated string
            products = [p.strip() for p in product_str.split(",")]
        else:
            # Fallback
            products = [str(product_str)]
            
        for product in products:
            if product:
                # Create product node
                product_node = Node("Product", name=product)
                graph.merge(product_node, "Product", "name")
                
                # Create OFFERS relationship between vendor and product
                offers_rel = Relationship(vendor_node, "OFFERS", product_node)
                graph.merge(offers_rel)
                
                # Create ABOUT relationship between email and product
                about_rel = Relationship(email_node, "ABOUT", product_node)
                graph.merge(about_rel)
        
        logging.info(f"Added email {email_id} to graph database")
        return True
    except Exception as e:
        logging.error(f"Failed to add email {email_id} to graph: {e}")
        return False

def import_all_emails():
    """Import all emails from ChromaDB to Neo4j"""
    graph = connect_to_graph()
    if not graph:
        return False
    
    create_schema(graph)
    
    # Get all emails from ChromaDB
    collection = llm_utils.get_chroma_collection()
    all_data = collection.get()
    
    # Group by email_id to avoid duplicates
    email_groups = {}
    for i, meta in enumerate(all_data["metadatas"]):
        email_id = meta.get("email_id")
        if email_id:
            if email_id not in email_groups:
                email_groups[email_id] = meta
    
    # Add each email to the graph
    success_count = 0
    for email_id, metadata in email_groups.items():
        if add_email_to_graph(graph, email_id, metadata):
            success_count += 1
    
    logging.info(f"Imported {success_count}/{len(email_groups)} emails to graph database")
    return True

def run_graph_query(query, params=None):
    """Run a Cypher query against the graph database"""
    graph = connect_to_graph()
    if not graph:
        return None
    
    try:
        result = graph.run(query, parameters=params or {}).data()
        return result
    except Exception as e:
        logging.error(f"Failed to run graph query: {e}")
        return None

def get_vendor_products(vendor_name):
    """Get all products offered by a vendor"""
    query = """
    MATCH (v:Vendor {name: $vendor})-[:OFFERS]->(p:Product)
    RETURN p.name AS product
    """
    return run_graph_query(query, {"vendor": vendor_name})

def get_related_vendors(product_name):
    """Get vendors related to a product"""
    query = """
    MATCH (p:Product {name: $product})<-[:OFFERS]-(v:Vendor)
    RETURN v.name AS vendor
    """
    return run_graph_query(query, {"product": product_name})

def get_email_timeline(vendor_name=None, product_name=None, days=30):
    """Get timeline of emails for a vendor or product"""
    params = {"days": days}
    where_clause = ""
    
    if vendor_name:
        where_clause += "v.name = $vendor"
        params["vendor"] = vendor_name
    
    if product_name:
        if where_clause:
            where_clause += " AND "
        where_clause += "p.name = $product"
        params["product"] = product_name
    
    if where_clause:
        where_clause = "WHERE " + where_clause
    
    query = f"""
    MATCH (e:Email)-[:FROM]->(v:Vendor), (e)-[:ABOUT]->(p:Product)
    {where_clause}
    RETURN e.id AS email_id, e.date AS date, e.type AS type, 
           v.name AS vendor, p.name AS product
    ORDER BY e.date DESC
    LIMIT 10
    """
    return run_graph_query(query, params)

def count_vendor_emails(vendor_name):
    """Count emails from a specific vendor"""
    query = """
    MATCH (e:Email)-[:FROM]->(v:Vendor {name: $vendor})
    RETURN count(e) AS email_count
    """
    result = run_graph_query(query, {"vendor": vendor_name})
    return result[0]["email_count"] if result else 0

def count_recent_emails(vendor_name=None, days=7):
    """Count emails received in the past X days from a vendor"""
    params = {"days": days}
    
    if vendor_name:
        query = """
        MATCH (e:Email)-[:FROM]->(v:Vendor)
        WHERE v.name = $vendor
        AND e.date > datetime() - duration({days: $days})
        RETURN count(e) AS email_count
        """
        params["vendor"] = vendor_name
    else:
        query = """
        MATCH (e:Email)-[:FROM]->(v:Vendor)
        WHERE e.date > datetime() - duration({days: $days})
        RETURN count(e) AS email_count
        """
    
    result = run_graph_query(query, params)
    return result[0]["email_count"] if result else 0

def find_security_emails(days=30):
    """Find security/vulnerability emails from the past X days"""
    query = """
    MATCH (e:Email)-[:FROM]->(v:Vendor), (e)-[:ABOUT]->(p:Product)
    WHERE (e.type CONTAINS 'security' OR e.type CONTAINS 'vulnerability') 
      AND e.date > datetime() - duration({days: $days})
    RETURN DISTINCT e.id AS email_id, e.date AS date, v.name AS vendor, 
           p.name AS product, e.type AS type
    ORDER BY e.date DESC
    """
    return run_graph_query(query, {"days": days})

def get_all_graph_data():
    """Get all data from the Neo4j database"""
    graph = connect_to_graph()
    if not graph:
        return None
    
    try:
        # Get all vendors with email counts
        vendors = run_graph_query("""
        MATCH (v:Vendor)
        OPTIONAL MATCH (v)<-[:FROM]-(e:Email)
        WITH v, count(e) AS email_count
        RETURN v.name AS name, email_count
        ORDER BY v.name
        """)
        
        # Get all products with vendor counts
        products = run_graph_query("""
        MATCH (p:Product)
        OPTIONAL MATCH (p)<-[:OFFERS]-(v:Vendor)
        WITH p, count(v) AS vendor_count
        RETURN p.name AS name, vendor_count
        ORDER BY p.name
        """)
        
        # Get all emails
        emails = run_graph_query("""
        MATCH (e:Email)-[:FROM]->(v:Vendor)
        RETURN e.id AS id, e.date AS date, e.type AS type, v.name AS vendor
        ORDER BY e.date DESC
        LIMIT 100
        """)
        
        # Get all relationships
        relationships = run_graph_query("""
        MATCH (v:Vendor)-[:OFFERS]->(p:Product)
        WITH v, collect(p.name) AS products
        RETURN v.name AS vendor, products
        ORDER BY v.name
        """)
        
        return {
            "vendors": vendors,
            "products": products,
            "emails": emails,
            "relationships": relationships
        }
    except Exception as e:
        logging.error(f"Failed to get all graph data: {e}")
        return None

def get_graph_summary():
    """Get a summary of the Neo4j database"""
    graph = connect_to_graph()
    if not graph:
        return None
    
    try:
        summary = run_graph_query("""
        MATCH (n)
        WITH labels(n) AS label, count(n) AS count
        RETURN label, count
        ORDER BY count DESC
        """)
        
        relationships = run_graph_query("""
        MATCH ()-[r]->()
        WITH type(r) AS relationship_type, count(r) AS count
        RETURN relationship_type, count
        ORDER BY count DESC
        """)
        
        return {
            "node_counts": summary,
            "relationship_counts": relationships
        }
    except Exception as e:
        logging.error(f"Failed to get graph summary: {e}")
        return None

def mock_graph_data():
    """Create mock graph data for testing without Neo4j"""
    logging.info("Creating mock graph data for testing")
    
    # Mock vendor products
    vendor_products = [
        {"product": "vault"},
        {"product": "terraform"},
        {"product": "consul"}
    ]
    
    # Mock related vendors
    related_vendors = [
        {"vendor": "hashicorp"}
    ]
    
    # Mock email timeline
    email_timeline = [
        {
            "email_id": "f822d769-2d8f-4a20-bf86-35c650a367c9",
            "date": "2025-04-16T07:35:07",
            "type": "announcement, event, webinar, product update",
            "vendor": "hashicorp",
            "product": "vault"
        },
        {
            "email_id": "f822d769-2d8f-4a20-bf86-35c650a367c9",
            "date": "2025-04-16T07:35:07",
            "type": "announcement, event, webinar, product update",
            "vendor": "hashicorp",
            "product": "terraform"
        }
    ]
    
    return {
        "vendor_products": vendor_products,
        "related_vendors": related_vendors,
        "email_timeline": email_timeline
    }

if __name__ == "__main__":
    # Try to import emails to Neo4j
    success = import_all_emails()
    
    # Get summary of the database
    summary = get_graph_summary()
    if summary:
        print("\nGraph Database Summary:")
        print("Node counts:")
        for item in summary["node_counts"]:
            print(f"- {item['label']}: {item['count']}")
        
        print("\nRelationship counts:")
        for item in summary["relationship_counts"]:
            print(f"- {item['relationship_type']}: {item['count']}")
    
    # Get all data
    all_data = get_all_graph_data()
    if all_data:
        print("\nVendors:")
        for vendor in all_data["vendors"]:
            print(f"- {vendor['name']}: {vendor['email_count']} emails")
        
        print("\nProducts:")
        for product in all_data["products"][:5]:  # Show only first 5
            print(f"- {product['name']}")
        if len(all_data["products"]) > 5:
            print(f"  ... and {len(all_data['products']) - 5} more")
        
        print("\nRelationships:")
        for rel in all_data["relationships"]:
            print(f"- {rel['vendor']} offers: {', '.join(rel['products'])}")