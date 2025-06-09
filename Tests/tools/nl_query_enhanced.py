"""
Enhanced Natural Language Query Interface

This module provides a command-line interface for querying the vendor email database
using natural language queries, leveraging the unified search functionality.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import the unified search API
from Tests.tools.unified_search_api import (
    process_search_query,
    unified_search,
    get_vendor_products_enhanced
)

from graph_db import (
    count_vendor_emails,
    count_recent_emails,
    find_security_emails,
    run_graph_query
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def extract_vendor(query: str) -> Optional[str]:
    """Extract vendor name from query"""
    # First check for specific vendor names
    vendors = ["hashicorp", "palo alto", "google", "aws", "amazon", "microsoft", "dell", "ibm"]
    for vendor in vendors:
        if vendor in query.lower():
            return vendor
    
    # Then try pattern matching
    vendor_patterns = [
        r"from\s+(\w+)\s+vendor",
        r"from\s+vendor\s+(\w+)",
        r"from\s+(\w+)",
        r"vendor\s+(\w+)",
        r"the\s+vendor\s+(\w+)",
        r"does\s+(\w+)\s+offer",
        r"does\s+the\s+vendor\s+(\w+)",
        r"does\s+(\w+)\s+have",
        r"emails\s+from\s+(\w+)"
    ]
    
    for pattern in vendor_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match and match.group(1).lower() not in ["the", "all", "any", "recent"]:
            return match.group(1).lower()
    
    return None

def process_query(query: str) -> str:
    """Process natural language query and return appropriate response"""
    query_lower = query.lower()
    
    # List all vendors
    if re.search(r"list\s+all\s+vendors|show\s+vendors|all\s+vendors", query_lower):
        result = run_graph_query("MATCH (v:Vendor) RETURN v.name AS vendor ORDER BY v.name")
        if result:
            vendors = [r["vendor"] for r in result]
            return f"Available vendors ({len(vendors)}):\n- " + "\n- ".join(vendors)
        else:
            return "No vendors found in the database."
    
    # List all products
    elif re.search(r"list\s+all\s+products|show\s+products|all\s+products", query_lower):
        result = run_graph_query("MATCH (p:Product) RETURN p.name AS product ORDER BY p.name")
        if result:
            products = [r["product"] for r in result]
            return f"Available products ({len(products)}):\n- " + "\n- ".join(products[:20]) + (f"\n... and {len(products) - 20} more" if len(products) > 20 else "")
        else:
            return "No products found in the database."
    
    # Products from vendor - enhanced version
    elif re.search(r"products|offerings|offer", query_lower) and "list" in query_lower:
        vendor = extract_vendor(query)
        if vendor:
            products = get_vendor_products_enhanced(vendor)
            
            if products:
                product_names = [p["product"] for p in products]
                return f"{vendor} offers the following products: {', '.join(product_names)}"
            else:
                return f"No products found for {vendor}."
        else:
            return "Please specify a vendor in your query."
    
    # For all other queries, use the unified search
    else:
        # Process the query
        processed = process_search_query(query)
        
        # If it's a simple metadata query, handle it directly
        if "count" in query_lower or "how many" in query_lower:
            vendor = extract_vendor(query)
            days = processed["graph_filters"].get("days", 30) if "recent" in query_lower or "past" in query_lower else None
            
            if vendor:
                if days:
                    count = count_recent_emails(vendor, days)
                    return f"There are {count} emails from {vendor} in the past {days} days."
                else:
                    count = count_vendor_emails(vendor)
                    return f"There are {count} emails from {vendor}."
            elif "all" in query_lower or "overall" in query_lower:
                if days:
                    count = count_recent_emails(days=days)
                    return f"There are {count} emails from all vendors in the past {days} days."
                else:
                    result = run_graph_query("MATCH (e:Email) RETURN count(e) AS email_count")
                    count = result[0]["email_count"] if result else 0
                    return f"There are {count} emails from all vendors."
        
        # Run unified search for content-based queries
        results = unified_search(
            processed["query_text"],
            processed["filters"],
            processed["graph_filters"],
            top_k=5
        )
        
        # Format the response
        if results["documents"]:
            response = f"Found {len(results['documents'])} relevant emails:\n\n"
            
            for i, (doc, meta) in enumerate(zip(results["documents"][:3], results["metadatas"][:3])):
                response += f"Result #{i+1}:\n"
                response += f"- Vendor: {meta.get('vendor', 'N/A')}\n"
                response += f"- Product: {meta.get('product', 'N/A')}\n"
                response += f"- Type: {meta.get('type', 'N/A')}\n"
                response += f"- Date: {meta.get('date', 'N/A')}\n"
                response += f"- Excerpt: {doc[:150]}...\n\n"
            
            if results["related_entities"]["products"]:
                response += "Related products: "
                response += ", ".join([f"{p['product']} ({p['count']})" for p in results["related_entities"]["products"][:3]])
                response += "\n"
            
            return response
        else:
            return "I couldn't find any relevant information for your query. Try refining your search or asking about email counts, recent emails, security updates, or vendor products."

def main():
    """Main function to run the command-line interface"""
    print("Enhanced Natural Language Query Interface")
    print("Type 'exit' to quit\n")
    print("Example queries:")
    print("- How many emails from hashicorp vendor?")
    print("- Show me recent security updates")
    print("- What's new from hashicorp about terraform")
    print("- Show me webinars from the past week")
    print("- List all products from hashicorp")
    print("- List all vendors\n")
    
    while True:
        try:
            query = input("Query: ")
            if query.lower() == "exit":
                break
            
            response = process_query(query)
            print(f"\n{response}\n")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError processing query: {e}\n")

if __name__ == "__main__":
    main()