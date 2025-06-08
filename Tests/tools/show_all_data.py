"""
Script to display all data from the Neo4j database
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from graph_db import get_all_graph_data, get_graph_summary

def print_all_data():
    """Print all data from the Neo4j database"""
    
    # Get summary of the database
    summary = get_graph_summary()
    if summary:
        print("\n=== GRAPH DATABASE SUMMARY ===")
        print("\nNode counts:")
        for item in summary["node_counts"]:
            print(f"- {item['label']}: {item['count']}")
        
        print("\nRelationship counts:")
        for item in summary["relationship_counts"]:
            print(f"- {item['relationship_type']}: {item['count']}")
    
    # Get all data
    all_data = get_all_graph_data()
    if all_data:
        print("\n=== ALL GRAPH DATA ===")
        
        print("\nVendors:")
        for vendor in all_data["vendors"]:
            print(f"- {vendor['name']}: {vendor['email_count']} emails")
        
        print("\nProducts:")
        for product in all_data["products"]:
            print(f"- {product['name']} (vendors: {product['vendor_count']})")
        
        print("\nEmails:")
        for email in all_data["emails"][:10]:  # Show only first 10
            print(f"- {email['date']}: {email['vendor']} - {email['type']}")
        if len(all_data["emails"]) > 10:
            print(f"  ... and {len(all_data['emails']) - 10} more")
        
        print("\nVendor-Product Relationships:")
        for rel in all_data["relationships"]:
            print(f"- {rel['vendor']} offers: {', '.join(rel['products'])}")

if __name__ == "__main__":
    print_all_data()