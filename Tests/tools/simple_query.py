"""
Simple script to query all data from Neo4j
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from graph_db import connect_to_graph

def query_all_data():
    """Query and display all data from Neo4j"""
    graph = connect_to_graph()
    if not graph:
        print("Failed to connect to Neo4j")
        return
    
    # Get all vendors
    print("\n=== VENDORS ===")
    result = graph.run("""
    MATCH (v:Vendor)
    RETURN v.name AS name
    """).data()
    for row in result:
        print(f"- {row['name']}")
    
    # Get all products
    print("\n=== PRODUCTS ===")
    result = graph.run("""
    MATCH (p:Product)
    RETURN p.name AS name
    """).data()
    for row in result:
        print(f"- {row['name']}")
    
    # Get all emails
    print("\n=== EMAILS ===")
    result = graph.run("""
    MATCH (e:Email)
    RETURN e.id AS id, e.date AS date, e.type AS type
    """).data()
    for row in result:
        print(f"- {row['id']}: {row['date']} ({row['type']})")
    
    # Get vendor-product relationships
    print("\n=== VENDOR-PRODUCT RELATIONSHIPS ===")
    result = graph.run("""
    MATCH (v:Vendor)-[:OFFERS]->(p:Product)
    RETURN v.name AS vendor, p.name AS product
    """).data()
    
    # Group by vendor
    vendor_products = {}
    for row in result:
        vendor = row['vendor']
        product = row['product']
        if vendor not in vendor_products:
            vendor_products[vendor] = []
        vendor_products[vendor].append(product)
    
    # Print grouped results
    for vendor, products in vendor_products.items():
        print(f"- {vendor}: {', '.join(products)}")
    
    # Get email-vendor relationships
    print("\n=== EMAIL-VENDOR RELATIONSHIPS ===")
    result = graph.run("""
    MATCH (e:Email)-[:FROM]->(v:Vendor)
    RETURN e.id AS email, v.name AS vendor
    """).data()
    for row in result:
        print(f"- {row['email']} from {row['vendor']}")

if __name__ == "__main__":
    query_all_data()