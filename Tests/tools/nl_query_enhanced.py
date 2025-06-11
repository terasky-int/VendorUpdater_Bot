"""
Enhanced Natural Language Query Interface for VendorUpdater_Bot
"""

import sys
import os
import logging
from typing import Dict, Any, List, Optional

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.unified_search import process_search_query, unified_search, format_search_results
from graph_db import run_graph_query, get_vendor_products_by_confidence

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def nl_query(query: str) -> Dict[str, Any]:
    """
    Process a natural language query and return structured results
    
    Args:
        query: Natural language query text
    
    Returns:
        Structured answer based on query type
    """
    try:
        # Process the query
        processed = process_search_query(query)
        logging.info(f"Processed query: {processed}")
        logging.info(f"Filters: {processed['filters']}")
        
        query_lower = query.lower()
        
        # Determine query type
        query_type = "search"  # Default
        
        if "how many" in query_lower or "count" in query_lower:
            query_type = "count"
        elif "list" in query_lower or "what products" in query_lower:
            query_type = "list"
        
        # Handle different query types
        if query_type == "count":
            # Count emails
            vendor = processed["filters"].get("vendor")
            days = processed["graph_filters"].get("days", 30)
            
            count_query = """
            MATCH (e:Email)
            """
            
            where_clauses = []
            params = {}
            
            if vendor:
                count_query += "MATCH (e)-[:FROM]->(v:Vendor)\n"
                where_clauses.append("toLower(v.name) = toLower($vendor)")
                params["vendor"] = vendor
            
            if days:
                where_clauses.append("e.date > datetime() - duration({days: $days})")
                params["days"] = days
            
            if where_clauses:
                count_query += "WHERE " + " AND ".join(where_clauses) + "\n"
            
            count_query += "RETURN count(e) AS email_count"
            
            result = run_graph_query(count_query, params)
            count = result[0]["email_count"] if result else 0
            
            time_period = f"in the past {days} days" if days else ""
            vendor_str = f"from {vendor}" if vendor else ""
            
            answer = f"There are {count} emails {vendor_str} {time_period}."
            
            return {
                "answer": answer.strip(),
                "query_type": "count",
                "data": {
                    "count": count
                }
            }
            
        elif query_type == "list":
            # Check if listing vendors
            if "vendors" in query_lower:
                vendors_query = """
                MATCH (v:Vendor)
                RETURN v.name AS vendor
                ORDER BY v.name
                """
                vendors = run_graph_query(vendors_query)
                
                if vendors:
                    vendor_names = [v["vendor"] for v in vendors]
                    return {
                        "answer": f"Available vendors ({len(vendor_names)}):\n- " + "\n- ".join(vendor_names),
                        "query_type": "list",
                        "data": {
                            "vendors": vendor_names
                        }
                    }
            
            # List products (potentially filtered by vendor)
            vendor = processed["filters"].get("vendor")
            
            if vendor:
                # Use exact vendor name matching for product listing
                products_query = """
                MATCH (v:Vendor)-[:OFFERS]->(p:Product)
                WHERE toLower(v.name) = toLower($vendor)
                RETURN p.name AS product
                ORDER BY p.name
                """
                products = run_graph_query(products_query, {"vendor": vendor})
            else:
                # List all products
                products_query = """
                MATCH (p:Product)
                RETURN p.name AS product
                ORDER BY p.name
                """
                products = run_graph_query(products_query)
            
            if products:
                product_names = [p["product"] for p in products]
                
                # Format the response
                if len(product_names) > 20:
                    displayed_products = product_names[:20]
                    response = f"Available products ({len(product_names)}):\n- " + "\n- ".join(displayed_products)
                    response += f"\n... and {len(product_names) - 20} more"
                else:
                    response = f"Available products ({len(product_names)}):\n- " + "\n- ".join(product_names)
                
                return {
                    "answer": response,
                    "query_type": "list",
                    "data": {
                        "products": product_names
                    }
                }
            else:
                return {
                    "answer": f"No products found for vendor '{vendor}'." if vendor else "No products found.",
                    "query_type": "list",
                    "data": {
                        "products": []
                    }
                }
                
        else:
            # Default to search
            results = unified_search(
                processed["query_text"],
                processed["filters"],
                processed["graph_filters"],
                5
            )
            
            if results["documents"]:
                formatted = format_search_results(results)
                
                # Format the response
                response = f"Found {len(formatted['results'])} results for your query:\n\n"
                
                for i, result in enumerate(formatted["results"][:3]):  # Show top 3
                    doc = result["document"]
                    meta = result["metadata"]
                    
                    # Truncate document if too long
                    if len(doc) > 100:
                        doc = doc[:100] + "..."
                    
                    response += f"{i+1}. {doc}\n"
                    response += f"   Vendor: {meta.get('vendor', 'N/A')}, "
                    response += f"Product: {meta.get('product', 'N/A')}, "
                    response += f"Type: {meta.get('type', 'N/A')}\n\n"
                
                if len(formatted['results']) > 3:
                    response += f"... and {len(formatted['results']) - 3} more results."
                
                return {
                    "answer": response,
                    "query_type": "search",
                    "data": formatted
                }
            else:
                return {
                    "answer": "I couldn't find any relevant information for your query. Try refining your search or asking about email counts, recent emails, security updates, or vendor products.",
                    "query_type": "search",
                    "data": {}
                }
    
    except Exception as e:
        logging.error(f"Error processing natural language query: {e}")
        return {
            "answer": f"I encountered an error while processing your query: {str(e)}",
            "query_type": "error",
            "data": {}
        }

def main():
    """Run the natural language query interface"""
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
        query = input("Query: ")
        if query.lower() in ["exit", "quit", "q"]:
            break
        
        result = nl_query(query)
        print("\n" + result["answer"] + "\n")

if __name__ == "__main__":
    main()