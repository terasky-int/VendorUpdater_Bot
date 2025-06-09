"""
Unified Search Implementation - Test Module

This module implements a hybrid search approach that combines:
1. Vector search with metadata filtering
2. Graph database relationships
3. Natural language query processing
"""

import re
import logging
from typing import Dict, List, Optional, Any
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.hybrid_search import hybrid_search
from src import llm_utils
from graph_db import run_graph_query

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def process_search_query(query: str) -> Dict[str, Any]:
    """
    Process natural language query and extract search parameters
    
    Args:
        query: Natural language query
    
    Returns:
        Dict with query text and filters
    """
    query_lower = query.lower()
    
    # Extract time constraints
    time_filter = None
    if "past week" in query_lower:
        time_filter = 7
    elif "past month" in query_lower:
        time_filter = 30
    elif "recent" in query_lower:
        time_filter = 30  # Default "recent" to last 30 days
    
    # Extract vendor constraints - improved pattern matching
    vendor_filter = None
    # Look for specific vendor names
    vendors = ["hashicorp", "palo alto", "google", "aws", "amazon", "microsoft", "dell", "ibm"]
    for vendor in vendors:
        if vendor in query_lower:
            vendor_filter = vendor
            break
    
    # If no specific vendor found, try the generic pattern
    if not vendor_filter:
        vendor_match = re.search(r"from\s+(\w+)(?:\s|$)", query_lower)
        if vendor_match and vendor_match.group(1) not in ["the", "all", "any", "recent"]:
            vendor_filter = vendor_match.group(1)
    
    # Extract product constraints - improved pattern matching
    product_filter = None
    # Look for specific product names
    products = ["vault", "terraform", "consul", "nomad", "boundary", "waypoint", "packer"]
    for product in products:
        if product in query_lower:
            product_filter = product
            break
    
    # If no specific product found, try the generic pattern
    if not product_filter:
        product_match = re.search(r"about\s+(\w+)(?:\s|$)", query_lower)
        if product_match:
            product_filter = product_match.group(1)
    
    # Extract type constraints
    type_filter = None
    if "security" in query_lower or "vulnerabilit" in query_lower:
        type_filter = "security"
    elif "webinar" in query_lower:
        type_filter = "webinar"
    elif "announcement" in query_lower:
        type_filter = "announcement"
    elif "update" in query_lower:
        type_filter = "update"
    
    # Build filters
    filters = {}
    if vendor_filter:
        filters["vendor"] = vendor_filter
    if product_filter:
        filters["product"] = product_filter
    if type_filter:
        # ChromaDB doesn't support $contains, so we'll use exact matching
        # In production, you might want to use a more sophisticated approach
        filters["type"] = type_filter
    
    # Build graph filters
    graph_filters = {}
    if time_filter:
        graph_filters["days"] = time_filter
    
    return {
        "query_text": query,
        "filters": filters,
        "graph_filters": graph_filters
    }

def graph_enhanced_ranking(results: Dict[str, Any], query_text: str) -> Dict[str, Any]:
    """
    Enhance search ranking using graph relationships
    
    Args:
        results: Results from vector search
        query_text: Original query text
    
    Returns:
        Reranked results
    """
    # If no results, return as is
    if not results["documents"]:
        return results
        
    # Extract email IDs and document scores
    email_scores = {}
    for i, meta in enumerate(results["metadatas"]):
        email_id = meta.get("email_id")
        if email_id:
            if email_id not in email_scores:
                email_scores[email_id] = results["distances"][i]
            else:
                # Keep the highest score for each email
                email_scores[email_id] = max(email_scores[email_id], results["distances"][i])
    
    # Get graph importance scores
    graph_scores = {}
    if email_scores:
        query = """
        MATCH (e:Email)
        WHERE e.id IN $email_ids
        OPTIONAL MATCH (e)-[:ABOUT]->(p:Product)
        OPTIONAL MATCH (e)-[:FROM]->(v:Vendor)
        WITH e, count(p) AS product_count, v
        RETURN e.id AS email_id, product_count, v.name AS vendor
        """
        graph_results = run_graph_query(query, {"email_ids": list(email_scores.keys())})
        
        if graph_results:
            for result in graph_results:
                email_id = result["email_id"]
                # Simple graph score based on product mentions
                graph_scores[email_id] = result["product_count"] * 0.1
                
                # Boost score for recent emails
                if "date" in result and result["date"]:
                    # This is simplified - in production you'd parse the date and calculate recency
                    graph_scores[email_id] += 0.05
    
    # Combine vector and graph scores
    combined_scores = {}
    for email_id, score in email_scores.items():
        graph_score = graph_scores.get(email_id, 0)
        combined_scores[email_id] = score + graph_score
    
    # Rerank results
    reranked_results = {
        "documents": [],
        "metadatas": [],
        "distances": [],
        "ids": []
    }
    
    # Sort by combined score
    sorted_emails = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Rebuild results in new order
    for email_id, _ in sorted_emails:
        for i, meta in enumerate(results["metadatas"]):
            if meta.get("email_id") == email_id:
                reranked_results["documents"].append(results["documents"][i])
                reranked_results["metadatas"].append(results["metadatas"][i])
                reranked_results["distances"].append(results["distances"][i])
                reranked_results["ids"].append(results["ids"][i])
    
    # If no reranked results (could happen if email_ids don't match), return original
    if not reranked_results["documents"]:
        return results
        
    return reranked_results

def unified_search(query_text: str, filters: Optional[Dict[str, Any]] = None, 
                  graph_filters: Optional[Dict[str, Any]] = None, top_k: int = 5) -> Dict[str, Any]:
    """
    Unified search combining vector search and graph relationships
    
    Args:
        query_text: The search query text
        filters: Dict of metadata filters for vector search
        graph_filters: Dict of graph filters (vendor, product, type, date range)
        top_k: Number of results to return
    
    Returns:
        Dict with search results and related entities
    """
    try:
        # Step 1: Vector search with metadata filters
        vector_results = hybrid_search(query_text, filters, top_k)
    except Exception as e:
        logging.error(f"Vector search failed: {e}")
        # Initialize empty results
        vector_results = {
            "documents": [],
            "metadatas": [],
            "distances": [],
            "ids": []
        }
    
    # Step 2: Extract email IDs from vector results
    email_ids = []
    for meta in vector_results["metadatas"]:
        if "email_id" in meta and meta["email_id"] not in email_ids:
            email_ids.append(meta["email_id"])
    
    # Step 3: Find related entities in graph database
    related_entities = {"products": [], "vendors": []}
    
    try:
        if email_ids:
            # Find related products
            products_query = """
            MATCH (e:Email)-[:ABOUT]->(p:Product)
            WHERE e.id IN $email_ids
            RETURN p.name AS product, count(e) AS count
            ORDER BY count DESC
            """
            products_result = run_graph_query(products_query, {"email_ids": email_ids})
            if products_result:
                related_entities["products"] = products_result
            
            # Find related vendors
            vendors_query = """
            MATCH (e:Email)-[:FROM]->(v:Vendor)
            WHERE e.id IN $email_ids
            RETURN v.name AS vendor, count(e) AS count
            ORDER BY count DESC
            """
            vendors_result = run_graph_query(vendors_query, {"email_ids": email_ids})
            if vendors_result:
                related_entities["vendors"] = vendors_result
        
        # If no results from vector search, try graph search directly
        if not email_ids and graph_filters:
            days = graph_filters.get("days", 30)
            vendor = filters.get("vendor") if filters else None
            product = filters.get("product") if filters else None
            
            # Query for recent emails matching criteria
            graph_query = """
            MATCH (e:Email)
            """
            
            where_clauses = []
            if days:
                where_clauses.append("e.date > datetime() - duration({days: $days})")
            
            if vendor:
                graph_query += "MATCH (e)-[:FROM]->(v:Vendor)\n"
                where_clauses.append("v.name = $vendor")
            
            if product:
                graph_query += "MATCH (e)-[:ABOUT]->(p:Product)\n"
                where_clauses.append("p.name = $product")
            
            if where_clauses:
                graph_query += "WHERE " + " AND ".join(where_clauses) + "\n"
                
            graph_query += """
            RETURN DISTINCT e.id AS email_id, e.date AS date, e.type AS type
            ORDER BY e.date DESC
            LIMIT 5
            """
            
            params = {}
            if days:
                params["days"] = days
            if vendor:
                params["vendor"] = vendor
            if product:
                params["product"] = product
                
            graph_results = run_graph_query(graph_query, params)
            
            if graph_results:
                # Get these emails from ChromaDB
                email_ids = [result["email_id"] for result in graph_results]
                collection = llm_utils.get_chroma_collection()
                
                try:
                    chroma_results = collection.get(
                        ids=email_ids,
                        include=["documents", "metadatas"]
                    )
                    
                    if chroma_results and chroma_results["documents"]:
                        vector_results = {
                            "documents": chroma_results["documents"],
                            "metadatas": chroma_results["metadatas"],
                            "distances": [1.0] * len(chroma_results["documents"]),  # Placeholder
                            "ids": email_ids
                        }
                except Exception as e:
                    logging.error(f"Failed to get documents from ChromaDB: {e}")
    except Exception as e:
        logging.error(f"Error in graph search: {e}")
    
    # Step 4: Combine and return results
    return {
        "documents": vector_results["documents"],
        "metadatas": vector_results["metadatas"],
        "distances": vector_results["distances"],
        "ids": vector_results["ids"],
        "related_entities": related_entities
    }

def run_test_query(query: str):
    """
    Run a test query through the unified search pipeline
    
    Args:
        query: Natural language query
    """
    print(f"\n🔍 Testing query: '{query}'")
    
    try:
        # Step 1: Process the query
        processed = process_search_query(query)
        print(f"\n📝 Processed query:")
        print(f"  - Query text: {processed['query_text']}")
        print(f"  - Filters: {processed['filters']}")
        print(f"  - Graph filters: {processed['graph_filters']}")
        
        # Step 2: Run unified search
        results = unified_search(
            processed["query_text"],
            processed["filters"],
            processed["graph_filters"]
        )
        
        # Step 3: Apply graph-enhanced ranking
        reranked = graph_enhanced_ranking(results, processed["query_text"])
        
        # Print results
        print(f"\n📊 Search results:")
        print(f"  - Found {len(results['documents'])} documents")
        
        if results["documents"]:
            print("\n📄 Top results:")
            for i, (doc, meta) in enumerate(zip(reranked["documents"][:3], reranked["metadatas"][:3])):
                print(f"\n  Result #{i+1}:")
                print(f"  - Email ID: {meta.get('email_id', 'N/A')}")
                print(f"  - Vendor: {meta.get('vendor', 'N/A')}")
                print(f"  - Product: {meta.get('product', 'N/A')}")
                print(f"  - Type: {meta.get('type', 'N/A')}")
                print(f"  - Date: {meta.get('date', 'N/A')}")
                print(f"  - Excerpt: {doc[:100]}...")
        
        if results["related_entities"]:
            print("\n🔗 Related entities:")
            
            if results["related_entities"].get("products"):
                print("  Products:")
                for product in results["related_entities"]["products"][:5]:
                    print(f"    - {product['product']} ({product['count']} mentions)")
            
            if results["related_entities"].get("vendors"):
                print("  Vendors:")
                for vendor in results["related_entities"]["vendors"][:5]:
                    print(f"    - {vendor['vendor']} ({vendor['count']} mentions)")
    
    except Exception as e:
        logging.error(f"Error running test query: {e}")
        print(f"\n❌ Error: {e}")

def mock_data_test():
    """Run tests with mock data when no real data is available"""
    print("\n🧪 Running tests with mock data")
    
    # Create mock vector results
    mock_results = {
        "documents": [
            "HashiCorp is excited to announce the release of Vault Enterprise 1.19 and Terraform 1.11. These releases bring new features and improvements to enhance your security and infrastructure as code workflows.",
            "Vault Enterprise 1.19 introduces new security features including improved secret rotation workflows and enhanced audit capabilities.",
            "Terraform 1.11 brings ephemeral values for safer secrets management and improved state handling."
        ],
        "metadatas": [
            {"email_id": "e123", "vendor": "hashicorp", "product": "vault,terraform", "type": "announcement,product update", "date": "2025-06-01"},
            {"email_id": "e124", "vendor": "hashicorp", "product": "vault", "type": "security,product update", "date": "2025-06-02"},
            {"email_id": "e125", "vendor": "hashicorp", "product": "terraform", "type": "product update", "date": "2025-06-03"}
        ],
        "distances": [0.95, 0.87, 0.82],
        "ids": ["id1", "id2", "id3"],
        "related_entities": {
            "products": [
                {"product": "vault", "count": 2},
                {"product": "terraform", "count": 2}
            ],
            "vendors": [
                {"vendor": "hashicorp", "count": 3}
            ]
        }
    }
    
    # Print mock results
    print("\n📄 Mock search results:")
    for i, (doc, meta) in enumerate(zip(mock_results["documents"], mock_results["metadatas"])):
        print(f"\n  Result #{i+1}:")
        print(f"  - Email ID: {meta.get('email_id', 'N/A')}")
        print(f"  - Vendor: {meta.get('vendor', 'N/A')}")
        print(f"  - Product: {meta.get('product', 'N/A')}")
        print(f"  - Type: {meta.get('type', 'N/A')}")
        print(f"  - Date: {meta.get('date', 'N/A')}")
        print(f"  - Excerpt: {doc[:100]}...")
    
    print("\n🔗 Related entities:")
    print("  Products:")
    for product in mock_results["related_entities"]["products"]:
        print(f"    - {product['product']} ({product['count']} mentions)")
    
    print("  Vendors:")
    for vendor in mock_results["related_entities"]["vendors"]:
        print(f"    - {vendor['vendor']} ({vendor['count']} mentions)")

if __name__ == "__main__":
    # Test queries
    test_queries = [
        "Show me recent security updates",
        "What's new from hashicorp about terraform",
        "Show me webinars from the past week",
        "Tell me about vault updates"
    ]
    
    # Run real tests
    print("\n🧪 Running tests with real data")
    for query in test_queries:
        run_test_query(query)
        print("\n" + "-" * 80)
    
    # If no results were found, run mock test
    mock_data_test()