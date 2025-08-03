# test_neo4j_queries.py
import sys
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()  # Load .env file

from graph_db_consolidated import run_graph_query

def test_neo4j_queries():
    print("Testing Neo4j queries...")
    
    # Test 1: Email types and classes
    print("\n1. Email types and classes:")
    
    types = run_graph_query("MATCH (n:VendorEmailType) RETURN n.name AS name LIMIT 5")
    print(f"VendorEmailType: {types}")
    
    classes = run_graph_query("MATCH (n:VendorEmailClass) RETURN n.name AS name LIMIT 5")
    print(f"VendorEmailClass: {classes}")
    
    relations = run_graph_query("MATCH p=()-[r:SUBSET_OF]->() RETURN type(r) AS rel_type LIMIT 5")
    print(f"SUBSET_OF relations: {relations}")
    
    # Test 2: Vendors and products
    print("\n2. Vendors and products:")
    
    vendors = run_graph_query("MATCH (n:Vendor) RETURN n.name AS name LIMIT 5")
    print(f"Vendors: {vendors}")
    
    products = run_graph_query("MATCH (n:Product) RETURN n.name AS name LIMIT 5")
    print(f"Products: {products}")
    
    makes = run_graph_query("MATCH (v:Vendor)-[r:MAKES]->(p:Product) RETURN v.name AS vendor, p.name AS product LIMIT 5")
    print(f"MAKES relations: {makes}")

if __name__ == "__main__":
    test_neo4j_queries()
