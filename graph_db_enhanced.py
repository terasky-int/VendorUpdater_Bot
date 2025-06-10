"""
Enhanced Graph database integration for VendorUpdater_Bot with relationship validation
"""

import logging
import os
import yaml
import re
from src import llm_utils
from py2neo import Graph, Node, Relationship

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Confidence levels for relationships
CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"

def connect_to_graph():
    """Connect to Neo4j database"""
    try:
        # Import here to avoid circular imports
        from src.config_utils import get_neo4j_config
        
        # Get Neo4j configuration from environment variables
        neo4j_config = get_neo4j_config()
        
        # Log connection details
        logging.info(f"Connecting to Neo4j at {neo4j_config['uri']} with user {neo4j_config['user']}")
        
        # Simple direct connection - this approach is known to work
        graph = Graph(
            neo4j_config["uri"], 
            auth=(neo4j_config["user"], neo4j_config["password"])
        )
        
        # Test the connection with a simple query
        result = graph.run("RETURN 1 AS test").data()
        logging.info(f"Neo4j connection test successful: {result}")
        
        logging.info("Connected to Neo4j database")
        return graph
    except Exception as e:
        logging.error(f"Failed to connect to Neo4j: {e}")
        logging.error(f"Connection details: URI={neo4j_config['uri']}, USER={neo4j_config['user']}")
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

def load_vendor_products():
    """Load vendor products from config file"""
    try:
        with open("config/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        return config.get("product_classification", {}).get("vendors", {})
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {}

def validate_vendor_product(vendor, product):
    """Validate if a vendor-product relationship is known in the config"""
    vendor_products = load_vendor_products()
    
    # Case-insensitive vendor matching
    for known_vendor, products in vendor_products.items():
        if vendor.lower() in known_vendor.lower() or known_vendor.lower() in vendor.lower():
            # Case-insensitive product matching
            for known_product in products:
                if product.lower() == known_product.lower():
                    return CONFIDENCE_HIGH
    
    return CONFIDENCE_LOW

def analyze_text_for_relationships(text, vendor, product):
    """Analyze text to determine confidence in vendor-product relationship"""
    text_lower = text.lower()
    vendor_lower = vendor.lower()
    product_lower = product.lower()
    
    # Look for strong relationship indicators
    strong_patterns = [
        rf"{vendor_lower}.*?(?:announces|releases|offers|launches).*?{product_lower}",
        rf"{product_lower}.*?(?:by|from|offered by).*?{vendor_lower}",
        rf"{vendor_lower}'s.*?{product_lower}"
    ]
    
    for pattern in strong_patterns:
        if re.search(pattern, text_lower):
            return CONFIDENCE_MEDIUM
    
    # Check if they appear in the same sentence
    sentences = re.split(r'[.!?]', text_lower)
    for sentence in sentences:
        if vendor_lower in sentence and product_lower in sentence:
            return CONFIDENCE_LOW
    
    return None  # No relationship found in text

def add_email_to_graph_enhanced(graph, email_id, metadata, email_text=None):
    """Add email data to the graph database with relationship validation"""
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
                
                # Determine confidence level for this relationship
                confidence = validate_vendor_product(vendor, product)
                
                # If we have email text, analyze it for additional confidence
                if email_text and confidence != CONFIDENCE_HIGH:
                    text_confidence = analyze_text_for_relationships(email_text, vendor, product)
                    if text_confidence:
                        # Use the higher confidence level
                        confidence = text_confidence if text_confidence == CONFIDENCE_MEDIUM else confidence
                
                # Create ABOUT relationship between email and product
                about_rel = Relationship(email_node, "ABOUT", product_node)
                graph.merge(about_rel)
                
                # Only create OFFERS relationship if confidence is medium or high
                if confidence in [CONFIDENCE_HIGH, CONFIDENCE_MEDIUM]:
                    offers_rel = Relationship(vendor_node, "OFFERS", product_node, confidence=confidence)
                    graph.merge(offers_rel)
                    logging.info(f"Created OFFERS relationship between {vendor} and {product} with {confidence} confidence")
                else:
                    logging.info(f"Skipped low-confidence OFFERS relationship between {vendor} and {product}")
        
        logging.info(f"Added email {email_id} to graph database with enhanced validation")
        return True
    except Exception as e:
        logging.error(f"Failed to add email {email_id} to graph: {e}")
        return False

def import_all_emails_enhanced():
    """Import all emails from ChromaDB to Neo4j with enhanced validation"""
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
                email_groups[email_id] = {
                    "metadata": meta,
                    "text": all_data["documents"][i] if i < len(all_data["documents"]) else None
                }
    
    # Add each email to the graph
    success_count = 0
    for email_id, data in email_groups.items():
        if add_email_to_graph_enhanced(graph, email_id, data["metadata"], data["text"]):
            success_count += 1
    
    logging.info(f"Imported {success_count}/{len(email_groups)} emails to graph database with enhanced validation")
    return True

def get_vendor_products_by_confidence(vendor_name, min_confidence=CONFIDENCE_LOW):
    """Get products offered by a vendor with specified minimum confidence"""
    query = """
    MATCH (v:Vendor)-[r:OFFERS]->(p:Product)
    WHERE toLower(v.name) CONTAINS toLower($vendor)
    AND r.confidence IN $confidence_levels
    RETURN v.name AS vendor, p.name AS product, r.confidence AS confidence
    ORDER BY r.confidence DESC
    """
    
    # Determine which confidence levels to include
    confidence_levels = []
    if min_confidence == CONFIDENCE_LOW:
        confidence_levels = [CONFIDENCE_LOW, CONFIDENCE_MEDIUM, CONFIDENCE_HIGH]
    elif min_confidence == CONFIDENCE_MEDIUM:
        confidence_levels = [CONFIDENCE_MEDIUM, CONFIDENCE_HIGH]
    else:
        confidence_levels = [CONFIDENCE_HIGH]
    
    return run_graph_query(query, {"vendor": vendor_name, "confidence_levels": confidence_levels})

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

def cleanup_incorrect_relationships():
    """Clean up incorrect vendor-product relationships based on config validation"""
    graph = connect_to_graph()
    if not graph:
        return False
    
    try:
        # Get all vendor-product relationships
        query = """
        MATCH (v:Vendor)-[r:OFFERS]->(p:Product)
        RETURN v.name AS vendor, p.name AS product, id(r) AS rel_id
        """
        relationships = graph.run(query).data()
        
        # Load vendor products from config
        vendor_products = load_vendor_products()
        
        # Check each relationship against the config
        removed_count = 0
        for rel in relationships:
            vendor = rel["vendor"]
            product = rel["product"]
            rel_id = rel["rel_id"]
            
            is_valid = False
            for known_vendor, products in vendor_products.items():
                if (vendor.lower() in known_vendor.lower() or 
                    known_vendor.lower() in vendor.lower()):
                    for known_product in products:
                        if product.lower() == known_product.lower():
                            is_valid = True
                            break
                if is_valid:
                    break
            
            # Remove invalid relationships
            if not is_valid:
                delete_query = f"""
                MATCH ()-[r]-()
                WHERE id(r) = {rel_id}
                DELETE r
                """
                graph.run(delete_query)
                removed_count += 1
                logging.info(f"Removed incorrect relationship: {vendor} OFFERS {product}")
        
        logging.info(f"Cleaned up {removed_count} incorrect relationships")
        return True
    except Exception as e:
        logging.error(f"Failed to clean up relationships: {e}")
        return False

if __name__ == "__main__":
    # Clean up incorrect relationships
    cleanup_incorrect_relationships()
    
    # Re-import emails with enhanced validation
    import_all_emails_enhanced()