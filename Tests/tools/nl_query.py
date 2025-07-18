"""
Natural language query interface for analytical queries
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import re
import logging
from datetime import datetime, timedelta
from graph_db import (
    count_vendor_emails,
    count_recent_emails,
    find_security_emails,
    get_email_timeline,
    get_vendor_products,
    run_graph_query
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def extract_vendor(query):
    """Extract vendor name from query"""
    # First check for specific vendor names
    vendors = ["hashicorp", "palo alto", "google", "aws", "amazon", "microsoft", "dell", "ibm"]
    for vendor in vendors:
        if vendor in query.lower():
            return vendor
    
    # Then try pattern matching
    vendor_patterns = [
        r"for\s+(\w+)\s+vendor",  # Added pattern for "for hashicorp vendor"
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

def extract_time_period(query):
    """Extract time period from query"""
    # Check for specific time periods
    if re.search(r"past\s+week|last\s+7\s+days", query, re.IGNORECASE):
        return 7
    elif re.search(r"past\s+month|last\s+30\s+days", query, re.IGNORECASE):
        return 30
    elif re.search(r"past\s+(\d+)\s+days", query, re.IGNORECASE):
        match = re.search(r"past\s+(\d+)\s+days", query, re.IGNORECASE)
        return int(match.group(1))
    
    # Default to 30 days
    return 30

def process_query(query):
    """Process natural language query and return appropriate response"""
    query = query.lower()
    
    # List all vendors
    if re.search(r"list\s+all\s+vendors|show\s+vendors|all\s+vendors", query):
        result = run_graph_query("MATCH (v:Vendor) RETURN v.name AS vendor ORDER BY v.name")
        if result:
            vendors = [r["vendor"] for r in result]
            return f"Available vendors ({len(vendors)}):\n- " + "\n- ".join(vendors)
        else:
            return "No vendors found in the database."
    
    # List all products
    elif re.search(r"list\s+all\s+products|show\s+products|all\s+products", query):
        result = run_graph_query("MATCH (p:Product) RETURN p.name AS product ORDER BY p.name")
        if result:
            products = [r["product"] for r in result]
            return f"Available products ({len(products)}):\n- " + "\n- ".join(products[:20]) + (f"\n... and {len(products) - 20} more" if len(products) > 20 else "")
        else:
            return "No products found in the database."
            
    # List emails from vendor
    elif re.search(r"list\s+(?:all\s+)?emails\s+from", query):
        vendor = extract_vendor(query)
        if vendor:
            # Query to get emails from specific vendor
            cypher_query = f"""
            MATCH (v:Vendor {{name: '{vendor}'}})<-[:FROM]-(e:Email)
            RETURN e.subject AS subject, e.date AS date
            ORDER BY e.date DESC LIMIT 10
            """
            emails = run_graph_query(cypher_query)
            
            if emails:
                response = f"Recent emails from {vendor} ({len(emails)}):\n"
                for email in emails:
                    date = email["date"].split("T")[0] if "T" in email["date"] else email["date"]
                    response += f"- {date}: {email['subject']}\n"
                return response
            else:
                return f"No emails found from {vendor}."
        else:
            return "Please specify a vendor name in your query."
    
    # Count emails from vendor
    elif re.search(r"how\s+many\s+emails|email\s+count", query):
        vendor = extract_vendor(query)
        if vendor:
            count = count_vendor_emails(vendor)
            return f"There are {count} emails from {vendor}."
        elif "all" in query or "overall" in query:
            # Count all emails
            result = run_graph_query("MATCH (e:Email) RETURN count(e) AS email_count")
            count = result[0]["email_count"] if result else 0
            return f"There are {count} emails from all vendors."
        else:
            return "Please specify a vendor in your query."
    
    # Recent emails
    elif re.search(r"past|recent|last", query):
        days = extract_time_period(query)
        vendor = extract_vendor(query)
        
        if vendor:
            count = count_recent_emails(vendor, days)
            return f"There are {count} emails from {vendor} in the past {days} days."
        else:
            count = count_recent_emails(days=days)
            return f"There are {count} emails from all vendors in the past {days} days."
    
    # Security/vulnerability emails
    elif re.search(r"security|vulnerabilit|patch|update", query):
        days = extract_time_period(query)
        emails = find_security_emails(days)
        
        if emails:
            response = f"Found {len(emails)} security-related emails in the past {days} days:\n"
            for email in emails[:5]:  # Show only first 5 for brevity
                response += f"- {email['date']}: {email['vendor']} - {email['product']}\n"
            if len(emails) > 5:
                response += f"... and {len(emails) - 5} more"
            return response
        else:
            return f"No security-related emails found in the past {days} days."
    
    # Products from vendor
    elif re.search(r"products|offerings|offer|available", query):
        vendor = extract_vendor(query)
        if vendor:
            # Option to use config or graph database
            use_config = "config" in query.lower() or "accurate" in query.lower()
            
            if use_config:
                # Import the vendor products utility for config-based lookup
                sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                from vendor_products import get_vendor_products
                
                # Get products from config
                matched_vendor, products = get_vendor_products(vendor)
                
                if matched_vendor and products:
                    return f"{matched_vendor} offers the following products (from config): {', '.join(products)}"
                else:
                    return f"No products found for {vendor} in the configuration."
            else:
                # Use graph database for dynamic lookup
                query = f"""
                MATCH (v:Vendor)-[:OFFERS]->(p:Product)
                WHERE toLower(v.name) CONTAINS toLower('{vendor}')
                RETURN v.name AS vendor_name, p.name AS product
                """
                products = run_graph_query(query)
                
                if products:
                    # Group by actual vendor name
                    vendor_products = {}
                    for p in products:
                        v_name = p["vendor_name"]
                        if v_name not in vendor_products:
                            vendor_products[v_name] = []
                        vendor_products[v_name].append(p["product"])
                    
                    response = f"Products associated with '{vendor}' (from graph database):\n"
                    for v_name, prods in vendor_products.items():
                        response += f"\nVendor: {v_name}\n- " + "\n- ".join(prods)
                    
                    response += "\n\nNote: For accurate product list, use 'show config products for hashicorp'"
                    return response
                else:
                    return f"No products found for {vendor} in the graph database."
        else:
            return "Please specify a vendor in your query."
    
    # Default response
    else:
        return "I couldn't understand your query. Try asking about email counts, recent emails, security updates, or vendor products."

if __name__ == "__main__":
    print("Natural Language Query Interface")
    print("Type 'exit' to quit\n")
    print("Example queries:")
    print("- How many emails from hashicorp vendor?")
    print("- How many emails received in the past week?")
    print("- What products does the vendor exasol offer?")
    print("- What security updates were reported in the past month?")
    print("- List all vendors")
    print("- List all products\n")
    
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