"""
Rebuild all vendor-product relationships in Neo4j using the enhanced validation logic
"""

import os
import sys
import logging

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Import required modules
from graph_db_consolidated import connect_to_graph, run_graph_query, validate_vendor_product

def rebuild_relationships():
    """Rebuild all vendor-product relationships using the enhanced validation logic"""
    try:
        # Connect to Neo4j
        graph = connect_to_graph()
        if not graph:
            logging.error("Failed to connect to Neo4j")
            return False
        
        # Get all emails with their vendors and products
        query = """
        MATCH (e:Email)-[:FROM]->(v:Vendor), (e)-[:ABOUT]->(p:Product)
        RETURN DISTINCT v.name AS vendor, p.name AS product
        """
        
        results = run_graph_query(query)
        if not results:
            logging.error("No vendor-product pairs found")
            return False
        
        # Delete all existing OFFERS relationships
        delete_query = """
        MATCH ()-[r:OFFERS]->()
        DELETE r
        """
        graph.run(delete_query)
        logging.info("Deleted all existing OFFERS relationships")
        
        # Rebuild relationships with enhanced validation
        count = 0
        for item in results:
            vendor = item["vendor"]
            product = item["product"]
            
            # Use enhanced validation logic
            confidence = validate_vendor_product(vendor, product)
            
            # Create relationship with confidence
            create_query = """
            MATCH (v:Vendor {name: $vendor}), (p:Product {name: $product})
            MERGE (v)-[r:OFFERS {confidence: $confidence}]->(p)
            RETURN r
            """
            
            graph.run(create_query, {
                "vendor": vendor,
                "product": product,
                "confidence": confidence
            })
            
            count += 1
            logging.info(f"Created relationship: {vendor} OFFERS {product} with {confidence} confidence")
        
        logging.info(f"Rebuilt {count} vendor-product relationships")
        return True
    
    except Exception as e:
        logging.error(f"Error rebuilding relationships: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting relationship rebuild")
    success = rebuild_relationships()
    if success:
        logging.info("Relationship rebuild completed successfully")
    else:
        logging.error("Relationship rebuild failed")