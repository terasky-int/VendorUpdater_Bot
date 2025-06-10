"""
Unified Search Module

This module provides unified search functionality combining vector search and graph relationships.
"""

import re
import logging
from typing import Dict, List, Optional, Any

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
        # Use exact matching for type
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

def get_vendor_products_enhanced(vendor_name: str) -> List[Dict[str, Any]]:
    """
    Get products offered by a vendor using graph database
    
    Args:
        vendor_name: Name of the vendor
    
    Returns:
        List of products with their details
    """
    # First try direct graph query
    query = """
    MATCH (v:Vendor {name: $vendor})-[:OFFERS]->(p:Product)
    RETURN p.name AS product
    """
    products = run_graph_query(query, {"vendor": vendor_name})
    
    if not products:
        # Try with case-insensitive match
        query = """
        MATCH (v:Vendor)-[:OFFERS]->(p:Product)
        WHERE toLower(v.name) CONTAINS toLower($vendor)
        RETURN p.name AS product, v.name AS vendor
        """
        products = run_graph_query(query, {"vendor": vendor_name})
    
    return products or []

def search_by_nl_query(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Perform a search using natural language query
    
    Args:
        query: Natural language query
        top_k: Number of results to return
    
    Returns:
        Dict with search results and related entities
    """
    # Process the query to extract filters
    processed = process_search_query(query)
    
    # Run unified search
    results = unified_search(
        processed["query_text"],
        processed["filters"],
        processed["graph_filters"],
        top_k
    )
    
    return results