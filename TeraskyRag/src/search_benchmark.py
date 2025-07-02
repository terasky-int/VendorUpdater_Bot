"""
Benchmark script to compare performance between original and optimized search implementations
"""

import time
import logging
import argparse
from typing import List, Dict, Any

# Import both search implementations
from src.unified_search import unified_search as original_search
from src.optimized_search import unified_search as optimized_search

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Test queries
TEST_QUERIES = [
    "Show me recent security updates from hashicorp",
    "What are the latest terraform announcements?",
    "Find emails about vault from the past month",
    "Show me webinars about cloud security",
    "Any product updates from palo alto?",
    "Recent vulnerability patches for consul",
    "Show me all hashicorp events from last week",
    "What's new with AWS services?",
    "Find emails about microsoft azure",
    "Recent announcements about nomad"
]

def run_benchmark(queries: List[str], implementation, name: str) -> Dict[str, Any]:
    """Run benchmark on a search implementation"""
    results = {
        "name": name,
        "total_time": 0,
        "avg_time": 0,
        "queries": len(queries),
        "results_count": [],
        "query_times": []
    }
    
    for query in queries:
        start_time = time.time()
        search_result = implementation(query)
        elapsed = time.time() - start_time
        
        results["total_time"] += elapsed
        results["query_times"].append(elapsed)
        results["results_count"].append(len(search_result["documents"]))
        
        logging.info(f"{name}: Query '{query}' returned {len(search_result['documents'])} results in {elapsed:.2f}s")
    
    results["avg_time"] = results["total_time"] / len(queries)
    return results

def main():
    parser = argparse.ArgumentParser(description="Benchmark search implementations")
    parser.add_argument("--iterations", type=int, default=1, help="Number of iterations to run")
    parser.add_argument("--queries", type=int, default=len(TEST_QUERIES), help="Number of queries to use")
    args = parser.parse_args()
    
    # Use subset of queries if requested
    queries = TEST_QUERIES[:args.queries]
    
    # Run benchmarks
    logging.info(f"Running benchmark with {len(queries)} queries, {args.iterations} iterations each")
    
    original_results = {
        "name": "Original Search",
        "total_time": 0,
        "avg_time": 0,
        "queries": len(queries) * args.iterations,
        "results_count": [],
        "query_times": []
    }
    
    optimized_results = {
        "name": "Optimized Search",
        "total_time": 0,
        "avg_time": 0,
        "queries": len(queries) * args.iterations,
        "results_count": [],
        "query_times": []
    }
    
    # Run multiple iterations
    for i in range(args.iterations):
        logging.info(f"Iteration {i+1}/{args.iterations}")
        
        # Run original implementation
        logging.info("Testing original implementation...")
        orig_iter = run_benchmark(queries, original_search, "Original")
        original_results["total_time"] += orig_iter["total_time"]
        original_results["results_count"].extend(orig_iter["results_count"])
        original_results["query_times"].extend(orig_iter["query_times"])
        
        # Run optimized implementation
        logging.info("Testing optimized implementation...")
        opt_iter = run_benchmark(queries, optimized_search, "Optimized")
        optimized_results["total_time"] += opt_iter["total_time"]
        optimized_results["results_count"].extend(opt_iter["results_count"])
        optimized_results["query_times"].extend(opt_iter["query_times"])
    
    # Calculate final averages
    original_results["avg_time"] = original_results["total_time"] / original_results["queries"]
    optimized_results["avg_time"] = optimized_results["total_time"] / optimized_results["queries"]
    
    # Calculate improvement
    improvement = (1 - (optimized_results["avg_time"] / original_results["avg_time"])) * 100
    
    # Print results
    print("\n===== BENCHMARK RESULTS =====")
    print(f"Queries: {len(queries)}")
    print(f"Iterations: {args.iterations}")
    print(f"Total queries: {len(queries) * args.iterations}")
    print("\nOriginal Implementation:")
    print(f"  Total time: {original_results['total_time']:.2f}s")
    print(f"  Average time per query: {original_results['avg_time']:.2f}s")
    print(f"  Average results per query: {sum(original_results['results_count']) / len(original_results['results_count']):.1f}")
    print("\nOptimized Implementation:")
    print(f"  Total time: {optimized_results['total_time']:.2f}s")
    print(f"  Average time per query: {optimized_results['avg_time']:.2f}s")
    print(f"  Average results per query: {sum(optimized_results['results_count']) / len(optimized_results['results_count']):.1f}")
    print(f"\nPerformance improvement: {improvement:.1f}%")
    print("=============================")

if __name__ == "__main__":
    main()