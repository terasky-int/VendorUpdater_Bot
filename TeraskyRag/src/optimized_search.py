"""
Optimized search implementation for VendorUpdater_Bot

This module provides an optimized implementation of unified search that combines:
1. Vector search with metadata filtering
2. Graph database relationships
3. Parallel processing for improved performance
4. Caching for frequently accessed data
"""

import re
import logging
import time
import functools
import concurrent.futures
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from src.hybrid_search import hybrid_search
from src import llm_utils
# from graph_db_consolidated import run_graph_query

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Simple in-memory cache with TTL
_CACHE = {}
_CACHE_TTL = {}
DEFAULT_CACHE_TTL = 300  # 5 minutes
_NEO4J_CONNECTION = None

def run_graph_query_cached(query, params=None):
    """Run a graph query using the cached connection"""
    from graph_db_consolidated import run_graph_query as original_run_graph_query
    
    # Get cached connection
    graph = get_neo4j_connection()
    if not graph:
        return None
    
    try:
        result = graph.run(query, parameters=params or {}).data()
        return result
    except Exception as e:
        logging.error(f"Failed to run graph query: {e}")
        return None

def get_neo4j_connection():
    """Get a reusable Neo4j connection"""
    global _NEO4J_CONNECTION
    if _NEO4J_CONNECTION is None:
        from graph_db_consolidated import connect_to_graph
        _NEO4J_CONNECTION = connect_to_graph()
    return _NEO4J_CONNECTION

def cache_with_ttl(ttl_seconds=DEFAULT_CACHE_TTL):
    """Decorator to cache function results with a TTL"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check if result is in cache and not expired
            current_time = time.time()
            if key in _CACHE and _CACHE_TTL.get(key, 0) > current_time:
                logging.debug(f"Cache hit for {key}")
                return _CACHE[key]
            
            # Call the function and cache the result
            result = func(*args, **kwargs)
            _CACHE[key] = result
            _CACHE_TTL[key] = current_time + ttl_seconds
            
            # Clean expired cache entries periodically
            if len(_CACHE) % 10 == 0:  # Clean every 10 new entries
                _clean_expired_cache()
                
            return result
        return wrapper
    return decorator

def _clean_expired_cache():
    """Remove expired entries from cache"""
    current_time = time.time()
    expired_keys = [k for k, ttl in _CACHE_TTL.items() if ttl <= current_time]
    for k in expired_keys:
        if k in _CACHE:
            del _CACHE[k]
        if k in _CACHE_TTL:
            del _CACHE_TTL[k]
    logging.debug(f"Cleaned {len(expired_keys)} expired cache entries")

@cache_with_ttl(ttl_seconds=3600)  # Cache for 1 hour
def get_vendor_product_lists():
    """Get lists of known vendors and products from config"""
    # This could be extended to load from a database or config file
    vendors = ["hashicorp", "palo alto", "google", "aws", "amazon", "microsoft", "dell", "ibm"]
    products = ["vault", "terraform", "consul", "nomad", "boundary", "waypoint", "packer"]
    
    return vendors, products

@cache_with_ttl(ttl_seconds=3600)  # Cache for 1 hour
def get_type_keywords():
    """Get mapping of type keywords"""
    return {
        "security": ["security", "vulnerability", "patch", "vulnerabilit"],
        "webinar": ["webinar", "workshop", "session"],
        "announcement": ["announcement", "news", "release"],
        "update": ["update", "upgrade", "new version"],
        "event": ["event", "conference", "meetup"]
    }

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
    if "past week" in query_lower or "last week" in query_lower:
        time_filter = 7
    elif "past month" in query_lower or "last month" in query_lower:
        time_filter = 30
    elif "past year" in query_lower or "last year" in query_lower:
        time_filter = 365
    elif "recent" in query_lower:
        time_filter = 30  # Default "recent" to last 30 days
    
    # Get cached lists of vendors and products
    vendors, products = get_vendor_product_lists()
    
    # Extract vendor constraints - improved pattern matching
    vendor_filter = None
    # Look for specific vendor names
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
    type_keywords = get_type_keywords()
    
    for type_name, keywords in type_keywords.items():
        for keyword in keywords:
            if keyword in query_lower:
                type_filter = type_name
                break
        if type_filter:
            break
    
    # Build filters
    filters = {}
    if vendor_filter:
        filters["vendor"] = vendor_filter
    if product_filter:
        filters["product"] = {"$contains": product_filter}
    if type_filter:
        # Use contains operator for partial matching
        filters["type"] = {"$contains": type_filter}
    
    # Build graph filters
    graph_filters = {}
    if time_filter:
        graph_filters["days"] = time_filter
    
    return {
        "query_text": query,
        "filters": filters,
        "graph_filters": graph_filters
    }

def _perform_vector_search(query_text: str, filters: Optional[Dict[str, Any]], top_k: int) -> Dict[str, Any]:
    """Helper function to perform vector search for parallel execution"""
    try:
        # Fix filters format for ChromaDB compatibility
        processed_filters = {}
        if filters:
            for key, value in filters.items():
                if isinstance(value, dict) and "$contains" in value:
                    # ChromaDB doesn't support $contains, use $eq for exact match instead
                    processed_filters[key] = {"$eq": value["$contains"]}
                else:
                    # For direct equality
                    processed_filters[key] = {"$eq": value}
        
        return hybrid_search(query_text, processed_filters, top_k)
    except Exception as e:
        logging.error(f"Vector search failed: {e}")
        return {
            "documents": [],
            "metadatas": [],
            "distances": [],
            "ids": []
        }

def _perform_graph_search(email_ids: List[str]) -> Dict[str, List]:
    """Helper function to perform graph search for parallel execution"""
    if not email_ids:
        return {"products": [], "vendors": []}
    
    related_entities = {"products": [], "vendors": []}
    
    try:
        # Find related products
        products_query = """
        MATCH (e:Email)-[:ABOUT]->(p:Product)
        WHERE e.id IN $email_ids
        RETURN p.name AS product, count(e) AS count
        ORDER BY count DESC
        """
        products_result = run_graph_query_cached(products_query, {"email_ids": email_ids})
        if products_result:
            related_entities["products"] = products_result
        
        # Find related vendors
        vendors_query = """
        MATCH (e:Email)-[:FROM]->(v:Vendor)
        WHERE e.id IN $email_ids
        RETURN v.name AS vendor, count(e) AS count
        ORDER BY count DESC
        """
        vendors_result = run_graph_query_cached(vendors_query, {"email_ids": email_ids})
        if vendors_result:
            related_entities["vendors"] = vendors_result
    except Exception as e:
        logging.error(f"Error in graph search: {e}")
    
    return related_entities

def _perform_graph_importance_query(email_ids: List[str]) -> Dict[str, float]:
    """Helper function to get graph importance scores"""
    if not email_ids:
        return {}
    
    graph_scores = {}
    try:
        query = """
        MATCH (e:Email)
        WHERE e.id IN $email_ids
        OPTIONAL MATCH (e)-[:ABOUT]->(p:Product)
        OPTIONAL MATCH (e)-[:FROM]->(v:Vendor)
        WITH e, count(p) AS product_count, v, e.date AS date
        RETURN e.id AS email_id, product_count, v.name AS vendor, date
        """
        graph_results = run_graph_query_cached(query, {"email_ids": email_ids})
        
        if graph_results:
            for result in graph_results:
                email_id = result["email_id"]
                # Simple graph score based on product mentions
                graph_scores[email_id] = result["product_count"] * 0.1
                
                # Boost score for recent emails
                if "date" in result and result["date"]:
                    try:
                        # Parse date and calculate recency boost
                        date_str = result["date"]
                        if isinstance(date_str, str):
                            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            days_old = (datetime.now() - date_obj).days
                            # More recent emails get higher boost
                            recency_boost = max(0, 0.2 - (days_old * 0.01))
                            graph_scores[email_id] += recency_boost
                    except Exception as e:
                        # Default boost if date parsing fails
                        graph_scores[email_id] += 0.05
    except Exception as e:
        logging.error(f"Error getting graph importance scores: {e}")
    
    return graph_scores

def _perform_fallback_graph_search(graph_filters: Dict[str, Any], filters: Dict[str, Any], top_k: int) -> Dict[str, Any]:
    """Helper function to perform fallback graph search when vector search returns no results"""
    try:
        days = graph_filters.get("days", 30)
        
        # Extract vendor and product from filters, handling both direct values and operators
        vendor = None
        product = None
        
        if filters:
            if "vendor" in filters:
                if isinstance(filters["vendor"], dict) and "$eq" in filters["vendor"]:
                    vendor = filters["vendor"]["$eq"]
                else:
                    vendor = filters["vendor"]
                    
            if "product" in filters:
                if isinstance(filters["product"], dict):
                    if "$contains" in filters["product"]:
                        product = filters["product"]["$contains"]
                    elif "$eq" in filters["product"]:
                        product = filters["product"]["$eq"]
                else:
                    product = filters["product"]
        
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
            where_clauses.append("p.name CONTAINS $product")
        
        if where_clauses:
            graph_query += "WHERE " + " AND ".join(where_clauses) + "\n"
            
        graph_query += """
        RETURN DISTINCT e.id AS email_id, e.date AS date, e.type AS type
        ORDER BY e.date DESC
        LIMIT $limit
        """
        
        params = {"limit": top_k}
        if days:
            params["days"] = days
        if vendor:
            params["vendor"] = vendor
        if product:
            params["product"] = product
            
        graph_results = run_graph_query_cached(graph_query, params)
        
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
                    return {
                        "documents": chroma_results["documents"],
                        "metadatas": chroma_results["metadatas"],
                        "distances": [1.0] * len(chroma_results["documents"]),  # Placeholder
                        "ids": email_ids
                    }
            except Exception as e:
                logging.error(f"Failed to get documents from ChromaDB: {e}")
    except Exception as e:
        logging.error(f"Error in fallback graph search: {e}")
    
    return {
        "documents": [],
        "metadatas": [],
        "distances": [],
        "ids": []
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
    graph_scores = _perform_graph_importance_query(list(email_scores.keys()))
    
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
    
    # Create a mapping from email_id to document indices for faster lookup
    email_id_to_indices = {}
    for i, meta in enumerate(results["metadatas"]):
        email_id = meta.get("email_id")
        if email_id:
            if email_id not in email_id_to_indices:
                email_id_to_indices[email_id] = []
            email_id_to_indices[email_id].append(i)
    
    # Rebuild results in new order
    for email_id, _ in sorted_emails:
        if email_id in email_id_to_indices:
            for i in email_id_to_indices[email_id]:
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
    Optimized unified search combining vector search and graph relationships
    
    Args:
        query_text: The search query text
        filters: Dict of metadata filters for vector search
        graph_filters: Dict of graph filters (vendor, product, type, date range)
        top_k: Number of results to return
    
    Returns:
        Dict with search results and related entities
    """
    start_time = time.time()
    
    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Submit vector search task
        vector_search_future = executor.submit(
            _perform_vector_search, 
            query_text, 
            filters, 
            top_k * 2  # Get more results initially for better reranking
        )
        
        # Wait for vector search to complete
        vector_results = vector_search_future.result()
        
        # Extract email IDs from vector results
        email_ids = []
        for meta in vector_results["metadatas"]:
            if "email_id" in meta and meta["email_id"] not in email_ids:
                email_ids.append(meta["email_id"])
        
        # If no results from vector search, try graph search as fallback
        if not email_ids and graph_filters:
            fallback_future = executor.submit(
                _perform_fallback_graph_search,
                graph_filters or {},
                filters or {},
                top_k
            )
            vector_results = fallback_future.result()
            
            # Extract email IDs from fallback results
            email_ids = []
            for meta in vector_results["metadatas"]:
                if "email_id" in meta and meta["email_id"] not in email_ids:
                    email_ids.append(meta["email_id"])
        
        # Submit graph search task for related entities
        graph_search_future = executor.submit(_perform_graph_search, email_ids)
        
        # Get related entities from graph search
        related_entities = graph_search_future.result()
    
    # Log performance metrics
    elapsed_time = time.time() - start_time
    logging.info(f"Unified search completed in {elapsed_time:.2f} seconds with {len(vector_results['documents'])} results")
    
    # Return combined results
    return {
        "documents": vector_results["documents"],
        "metadatas": vector_results["metadatas"],
        "distances": vector_results["distances"],
        "ids": vector_results["ids"],
        "related_entities": related_entities
    }

@cache_with_ttl(ttl_seconds=600)  # Cache for 10 minutes
def get_vendor_products_enhanced(vendor_name: str) -> List[Dict[str, Any]]:
    """
    Get products offered by a vendor with confidence levels
    
    Args:
        vendor_name: Name of the vendor
    
    Returns:
        List of products with confidence levels
    """
    try:
        from graph_db_consolidated import get_vendor_products_by_confidence
        
        # Try to get products with confidence levels
        products = get_vendor_products_by_confidence(vendor_name)
        
        if products:
            return products
        
        # Fall back to regular product lookup
        from graph_db_consolidated import get_vendor_products
        basic_products = get_vendor_products(vendor_name)
        
        if basic_products:
            # Convert to enhanced format
            return [
                {"vendor": vendor_name, "product": p["product"], "confidence": "unknown"}
                for p in basic_products
            ]
        
        return []
    except Exception as e:
        logging.error(f"Error getting vendor products: {e}")
        return []

def format_search_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format search results for API response
    
    Args:
        results: Raw search results
    
    Returns:
        Formatted results for API response
    """
    formatted_results = []
    
    for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"])):
        formatted_results.append({
            "document": doc,
            "metadata": meta,
            "score": results["distances"][i] if i < len(results["distances"]) else 0.0
        })
    
    return {
        "results": formatted_results,
        "related_entities": results["related_entities"],
        "total_results": len(formatted_results)
    }