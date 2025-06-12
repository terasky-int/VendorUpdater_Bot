"""
Fix missing vendor-product relationships in Neo4j
"""

import os
import sys
import logging

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Import required modules
from graph_db_consolidated import connect_to_graph, run_graph_query, CONFIDENCE_HIGH

def fix_vendor_product_relationships():
    """Fix missing vendor-product relationships in Neo4j"""
    try:
        # Connect to Neo4j
        graph = connect_to_graph()
        if not graph:
            logging.error("Failed to connect to Neo4j")
            return False
        
        # Define known vendor-product relationships
        known_relationships = {
            "hashicorp": [
                "radar", "Vault Enterprise", "Terraform", "flex", "hcp vault radar",
                "vault", "terraform", "boundary", "consul", "nomad", "packer", 
                "waypoint", "sentinel", "terraform cloud"
            ],
            "dell": ["DELL"],
            "amazon": ["Amazon Bedrock", "Amazon SageMaker", "Amazon Q", "AWS Summit Tel Aviv 2025", "Route 53"],
            "cellebrite": ["Cellebrite"],
            "goteleport": ["Teleport"],
            "prompt": ["Prompt Security"],
            "paloaltonetworks": [
                "prisma cloud", "Prisma Certified Cloud Security Engineer", 
                "Palo Alto Networks Certification", "Palo Alto Networks Accreditation",
                "Cortex XDR Agent", "Cortex", "Prisma Cloud"
            ],
            "broadcom": ["VMware Cloud Foundation"]
        }
        
        # Count relationships before fix
        count_before = run_graph_query("""
        MATCH ()-[r:OFFERS]->()
        RETURN count(r) AS count
        """)
        
        relationships_added = 0
        
        # Process each vendor and its products
        for vendor, products in known_relationships.items():
            # Check if vendor exists
            vendor_check = run_graph_query(
                "MATCH (v:Vendor {name: $vendor}) RETURN v",
                {"vendor": vendor}
            )
            
            if not vendor_check:
                # Create vendor if it doesn't exist
                create_vendor_query = """
                CREATE (v:Vendor {name: $vendor})
                RETURN v
                """
                run_graph_query(create_vendor_query, {"vendor": vendor})
                logging.info(f"Created vendor node: {vendor}")
            
            # Process each product
            for product in products:
                # Check if product exists
                product_check = run_graph_query(
                    "MATCH (p:Product {name: $product}) RETURN p",
                    {"product": product}
                )
                
                if not product_check:
                    # Create product if it doesn't exist
                    create_product_query = """
                    CREATE (p:Product {name: $product})
                    RETURN p
                    """
                    run_graph_query(create_product_query, {"product": product})
                    logging.info(f"Created product node: {product}")
                
                # Create OFFERS relationship with high confidence
                create_rel_query = """
                MATCH (v:Vendor {name: $vendor}), (p:Product {name: $product})
                MERGE (v)-[r:OFFERS {confidence: $confidence}]->(p)
                RETURN r
                """
                result = run_graph_query(
                    create_rel_query, 
                    {"vendor": vendor, "product": product, "confidence": CONFIDENCE_HIGH}
                )
                
                if result:
                    relationships_added += 1
                    logging.info(f"Created relationship: {vendor} OFFERS {product}")
        
        # Count relationships after fix
        count_after = run_graph_query("""
        MATCH ()-[r:OFFERS]->()
        RETURN count(r) AS count
        """)
        
        before_count = count_before[0]["count"] if count_before else 0
        after_count = count_after[0]["count"] if count_after else 0
        
        logging.info(f"Relationships before fix: {before_count}")
        logging.info(f"Relationships after fix: {after_count}")
        logging.info(f"Added {relationships_added} relationships")
        
        return True
    
    except Exception as e:
        logging.error(f"Error fixing relationships: {e}")
        return False

def verify_fixes():
    """Verify that the fixes were applied correctly"""
    try:
        # Check for vendors without products
        vendors_no_products_query = """
        MATCH (v:Vendor)
        WHERE NOT (v)-[:OFFERS]->(:Product)
        RETURN v.name AS vendor
        """
        vendors_no_products = run_graph_query(vendors_no_products_query)
        
        # Check for products without vendors
        products_no_vendors_query = """
        MATCH (p:Product)
        WHERE NOT (p)<-[:OFFERS]-(:Vendor)
        RETURN p.name AS product
        """
        products_no_vendors = run_graph_query(products_no_vendors_query)
        
        print("\n=== Verification Results ===")
        
        print("\nVendors still without products:")
        if vendors_no_products:
            for result in vendors_no_products:
                print(f"- {result['vendor']}")
        else:
            print("- None found")
        
        print("\nProducts still without vendors:")
        if products_no_vendors:
            for result in products_no_vendors:
                print(f"- {result['product']}")
        else:
            print("- None found")
        
        return {
            "vendors_without_products": [r["vendor"] for r in vendors_no_products] if vendors_no_products else [],
            "products_without_vendors": [r["product"] for r in products_no_vendors] if products_no_vendors else []
        }
    
    except Exception as e:
        logging.error(f"Error verifying fixes: {e}")
        return None

if __name__ == "__main__":
    logging.info("Starting relationship fix")
    
    # Fix relationships
    success = fix_vendor_product_relationships()
    
    if success:
        # Verify fixes
        verification = verify_fixes()
        
        logging.info("Relationship fix complete")
    else:
        logging.error("Failed to fix relationships")