#!/usr/bin/env python3
"""
Comprehensive test runner for VendorUpdater_Bot
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import logging
import json
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_debug_search():
    """Run debug search to inspect ChromaDB collection"""
    logging.info("Running debug search...")
    import debug_search
    debug_search.inspect_chroma_collection()
    debug_search.test_basic_search()

def load_sample_data():
    """Load sample test data into ChromaDB"""
    logging.info("Loading sample test data...")
    import load_test_data
    load_test_data.load_test_data()

def test_search_quality():
    """Test search quality with the test queries"""
    logging.info("Testing search quality...")
    import test_search_quality
    results = test_search_quality.evaluate_search()
    
    # Print summary
    basic_results = results["basic"]
    filtered_results = results["filtered"]
    
    print("\n=== SEARCH QUALITY SUMMARY ===")
    print(f"Basic search success rate: {sum(1 for r in basic_results.values() if r['vector_count'] > 0)}/{len(basic_results)}")
    print(f"Filtered search success rate: {sum(1 for r in filtered_results.values() if r['result_count'] > 0)}/{len(filtered_results)}")
    
    # Calculate average keyword coverage
    coverages = [r["coverage"] for r in filtered_results.values()]
    avg_coverage = sum(coverages) / len(coverages) if coverages else 0
    print(f"Average keyword coverage: {avg_coverage:.2f}")

def test_rag_api():
    """Test the RAG API endpoints"""
    logging.info("Testing RAG API endpoints...")
    import requests
    import subprocess
    import time
    import signal
    
    # Start the API server in the background
    api_process = subprocess.Popen([sys.executable, "../../rag_api.py"])
    time.sleep(3)  # Give it time to start
    
    try:
        # Test health endpoint
        health_response = requests.get("http://localhost:8000/health")
        print(f"Health check: {health_response.status_code}")
        print(health_response.json())
        
        # Test metadata endpoint
        metadata_response = requests.get("http://localhost:8000/metadata")
        print(f"Metadata: {metadata_response.status_code}")
        print(json.dumps(metadata_response.json(), indent=2))
        
        # Test queries that match our actual data
        test_queries = [
            {
                "query": "palo alto certification test",
                "metadata_filters": {"vendor": "paloaltonetworks"}
            },
            {
                "query": "google cloud event test",
                "metadata_filters": {"vendor": "google"}
            },
            {
                "query": "hashicorp vault workshop test",
                "metadata_filters": {"vendor": "hashicorp"}
            },
            {
                "query": "terraform cloud migration test",
                "metadata_filters": {"product": "vault, terraform, boundary, consul, nomad, packer, waypoint, sentinel, terraform cloud"}
            }
        ]
        
        for query_data in test_queries:
            print(f"\nTesting query: {query_data['query']}")
            query_response = requests.post("http://localhost:8000/query", json=query_data)
            print(f"Status: {query_response.status_code}")
            if query_response.status_code == 200:
                result = query_response.json()
                print(f"Answer: {result['answer']}")
                print(f"Sources: {len(result['sources'])}")
                if result['sources']:
                    print(f"First source metadata: {result['sources'][0]['metadata']}")
    finally:
        # Kill the API server
        api_process.send_signal(signal.SIGTERM)
        api_process.wait()

def run_all_tests():
    """Run all tests in sequence"""
    run_debug_search()
    test_search_quality()
    test_rag_api()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests for VendorUpdater_Bot")
    parser.add_argument("--debug", action="store_true", help="Run debug search")
    parser.add_argument("--load-data", action="store_true", help="Load sample test data")
    parser.add_argument("--search", action="store_true", help="Test search quality")
    parser.add_argument("--api", action="store_true", help="Test RAG API")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    if args.all:
        run_all_tests()
    else:
        if args.debug:
            run_debug_search()
        if args.load_data:
            load_sample_data()
        if args.search:
            test_search_quality()
        if args.api:
            test_rag_api()
        
        # If no specific test was selected, show help
        if not (args.debug or args.load_data or args.search or args.api):
            parser.print_help()