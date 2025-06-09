"""
Debug tool to analyze vendor-product relationships in the graph database
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from graph_db import run_graph_query

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def analyze_vendor_products(vendor_name):
    """Analyze products associated with a vendor and their sources"""
    
    # Get all products associated with the vendor
    query = """
    MATCH (v:Vendor)-[:OFFERS]->(p:Product)
    WHERE toLower(v.name) CONTAINS toLower($vendor)
    RETURN v.name AS vendor, p.name AS product
    """
    products = run_graph_query(query, {"vendor": vendor_name})
    
    if not products:
        print(f"No products found for vendor '{vendor_name}'")
        return
    
    print(f"\nProducts associated with '{vendor_name}' in graph database:")
    for p in products:
        print(f"- {p['product']} (from vendor: {p['vendor']})")
    
    # Find emails that created these relationships
    print("\nAnalyzing source emails for these relationships:")
    
    for p in products:
        product = p['product']
        query = """
        MATCH (e:Email)-[:ABOUT]->(p:Product {name: $product})
        MATCH (e)-[:FROM]->(v:Vendor)
        WHERE toLower(v.name) CONTAINS toLower($vendor)
        RETURN e.id AS email_id, e.date AS date, e.type AS type, v.name AS vendor
        LIMIT 3
        """
        emails = run_graph_query(query, {"product": product, "vendor": vendor_name})
        
        print(f"\nProduct: {product}")
        if emails:
            for e in emails:
                print(f"  - Email ID: {e['email_id']}")
                print(f"    Date: {e['date']}")
                print(f"    Type: {e['type']}")
                print(f"    Vendor: {e['vendor']}")
        else:
            print("  No source emails found")
    
    # Check for incorrect relationships
    print("\nChecking for potential incorrect relationships:")
    query = """
    MATCH (v:Vendor)-[:OFFERS]->(p:Product)
    WHERE toLower(v.name) CONTAINS toLower($vendor)
    WITH v, p
    MATCH (e:Email)-[:ABOUT]->(p)
    MATCH (e)-[:FROM]->(other:Vendor)
    WHERE other <> v
    RETURN p.name AS product, other.name AS other_vendor, count(e) AS count
    ORDER BY count DESC
    """
    incorrect = run_graph_query(query, {"vendor": vendor_name})
    
    if incorrect:
        print("\nPotential incorrect relationships:")
        for i in incorrect:
            print(f"- Product '{i['product']}' is associated with vendor '{i['other_vendor']}' in {i['count']} emails")
    else:
        print("\nNo potential incorrect relationships found")

if __name__ == "__main__":
    print("Vendor-Product Relationship Analyzer")
    
    if len(sys.argv) > 1:
        vendor = sys.argv[1]
    else:
        vendor = input("Enter vendor name to analyze: ")
    
    analyze_vendor_products(vendor)