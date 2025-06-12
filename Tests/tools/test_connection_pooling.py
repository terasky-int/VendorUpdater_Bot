"""
Test script to verify Neo4j connection pooling in optimized_search.py
"""

import sys
import os
import time
import logging

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def test_connection_pooling():
    """Test that the Neo4j connection is reused across multiple queries"""
    from src.optimized_search import get_neo4j_connection, run_graph_query_cached
    
    # First connection
    logging.info("Getting first connection...")
    start_time = time.time()
    conn1 = get_neo4j_connection()
    first_conn_time = time.time() - start_time
    logging.info(f"First connection established in {first_conn_time:.4f} seconds")
    
    # Run a simple query
    logging.info("Running first query...")
    start_time = time.time()
    result1 = run_graph_query_cached("RETURN 1 AS test")
    first_query_time = time.time() - start_time
    logging.info(f"First query completed in {first_query_time:.4f} seconds: {result1}")
    
    # Second connection (should be cached)
    logging.info("Getting second connection (should be cached)...")
    start_time = time.time()
    conn2 = get_neo4j_connection()
    second_conn_time = time.time() - start_time
    logging.info(f"Second connection retrieved in {second_conn_time:.4f} seconds")
    
    # Run another query
    logging.info("Running second query...")
    start_time = time.time()
    result2 = run_graph_query_cached("RETURN 2 AS test")
    second_query_time = time.time() - start_time
    logging.info(f"Second query completed in {second_query_time:.4f} seconds: {result2}")
    
    # Check if connections are the same object
    is_same_connection = conn1 is conn2
    logging.info(f"Are connections the same object? {is_same_connection}")
    
    # Compare times
    logging.info(f"Connection time comparison: First={first_conn_time:.4f}s, Second={second_conn_time:.4f}s")
    logging.info(f"Query time comparison: First={first_query_time:.4f}s, Second={second_query_time:.4f}s")
    
    return {
        "is_same_connection": is_same_connection,
        "first_conn_time": first_conn_time,
        "second_conn_time": second_conn_time,
        "first_query_time": first_query_time,
        "second_query_time": second_query_time
    }

def test_search_with_pooling():
    """Test that the unified search function uses the connection pool"""
    from src.optimized_search import unified_search, process_search_query
    
    # Process a search query
    logging.info("Processing search query...")
    query = "Show me recent emails about Terraform from HashiCorp"
    search_params = process_search_query(query)
    
    # Run the search
    logging.info("Running unified search...")
    start_time = time.time()
    results = unified_search(
        search_params["query_text"],
        search_params["filters"],
        search_params["graph_filters"]
    )
    search_time = time.time() - start_time
    
    logging.info(f"Search completed in {search_time:.4f} seconds")
    logging.info(f"Found {len(results['documents'])} results")
    
    return {
        "search_time": search_time,
        "result_count": len(results["documents"])
    }

if __name__ == "__main__":
    logging.info("Testing Neo4j connection pooling...")
    
    # Test basic connection pooling
    pooling_results = test_connection_pooling()
    
    # Test search with pooling
    search_results = test_search_with_pooling()
    
    # Print summary
    logging.info("\n=== Connection Pooling Test Results ===")
    logging.info(f"Connection reuse: {'SUCCESS' if pooling_results['is_same_connection'] else 'FAILED'}")
    logging.info(f"First connection time: {pooling_results['first_conn_time']:.4f}s")
    logging.info(f"Second connection time: {pooling_results['second_conn_time']:.4f}s")
    logging.info(f"Connection time reduction: {(1 - pooling_results['second_conn_time']/pooling_results['first_conn_time'])*100:.1f}%")
    logging.info(f"Search execution time: {search_results['search_time']:.4f}s")
    logging.info(f"Search results count: {search_results['result_count']}")