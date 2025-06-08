"""
Script to run custom Cypher queries against the Neo4j database
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from graph_db import run_graph_query

def run_custom_query(query):
    """Run a custom Cypher query and print the results"""
    print(f"\nRunning query: {query}")
    
    results = run_graph_query(query)
    if results:
        print(f"\nFound {len(results)} results:")
        
        # Print column headers
        if results:
            headers = list(results[0].keys())
            header_str = " | ".join(headers)
            print("\n" + header_str)
            print("-" * len(header_str))
        
        # Print rows
        for row in results:
            values = []
            for key in headers:
                value = row.get(key, "")
                if isinstance(value, list):
                    value = ", ".join(map(str, value))
                values.append(str(value))
            print(" | ".join(values))
    else:
        print("No results found or query failed.")

def interactive_mode():
    """Run in interactive mode, accepting queries from the user"""
    print("Neo4j Cypher Query Tool")
    print("Type 'exit' to quit")
    print("Enter complete queries in a single line\n")
    print("Example queries:")
    print("  MATCH (e:Email)-[:FROM]->(v:Vendor) RETURN v.name AS vendor, count(e) AS email_count ORDER BY email_count DESC")
    print("  MATCH (v:Vendor)-[:OFFERS]->(p:Product) RETURN v.name AS vendor, count(p) AS product_count ORDER BY product_count DESC\n")
    
    while True:
        try:
            query = input("cypher> ")
            if query.lower() in ("exit", "quit"):
                break
            
            # Skip comments
            if query.strip().startswith("//"):
                continue
                
            run_custom_query(query)
            print()
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run the query provided as command line argument
        query = " ".join(sys.argv[1:])
        run_custom_query(query)
    else:
        # Run in interactive mode
        interactive_mode()