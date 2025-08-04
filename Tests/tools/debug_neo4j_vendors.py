"""
Debug script to see vendor nodes in Neo4j and their email relationships
"""

import os
import sys

# Add parent directories to path and change working directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(project_root)
os.chdir(project_root)

from graph_db_consolidated import connect_to_graph, run_graph_query

def debug_neo4j_vendors():
    # Get all vendor nodes
    vendors_query = """
    MATCH (v:Vendor)
    OPTIONAL MATCH (v)<-[:SENT_BY]-(e:VendorEmail)
    WITH v, count(e) AS email_count
    RETURN v.name AS vendor, email_count
    ORDER BY email_count DESC
    """
    
    vendors = run_graph_query(vendors_query)
    
    print("=== Vendor Nodes in Neo4j ===")
    if vendors:
        for vendor in vendors:
            print(f"{vendor['vendor']}: {vendor['email_count']} emails")
    else:
        print("No vendor nodes found")
    
    # Get sample email data with vendors
    emails_query = """
    MATCH (e:VendorEmail)-[:SENT_BY]->(v:Vendor)
    RETURN e.vendor AS detected_vendor, v.name AS actual_vendor, e.sender AS sender
    LIMIT 10
    """
    
    emails = run_graph_query(emails_query)
    
    print("\n=== Sample Email-Vendor Mappings ===")
    if emails:
        for email in emails:
            print(f"Detected: '{email['detected_vendor']}' -> Actual: '{email['actual_vendor']}' | Sender: {email['sender']}")
    else:
        print("No email-vendor relationships found")

if __name__ == "__main__":
    debug_neo4j_vendors()