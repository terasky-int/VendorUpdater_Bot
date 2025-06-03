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
        logging.info("Connected to Neo4j database")
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
        
        # Handle multiple products (comma-separated)
        products = [p.strip() for p in product_str.split(",")]
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

if __name__ == "__main__":
    # Test the graph database integration
    import_all_emails()
    
    # Run some test queries
    print("\nVendor products:")
    products = get_vendor_products("hashicorp")
    print(products)
    
    print("\nRelated vendors:")
    vendors = get_related_vendors("vault")
    print(vendors)
    
    print("\nEmail timeline:")
    timeline = get_email_timeline(vendor_name="hashicorp")
    print(timeline)