import logging
import json
import os
from src.hybrid_search import hybrid_search

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Test queries with expected relevant document IDs - updated to match actual data
test_cases = [
    {
        "query": "palo alto certification",
        "filters": {"vendor": "paloaltonetworks"},
        "expected_keywords": ["palo", "alto", "certification", "accreditation"]
    },
    {
        "query": "google cloud event",
        "filters": {"vendor": "google"},
        "expected_keywords": ["google", "cloud", "event", "webinar"]
    },
    {
        "query": "cortex prisma security",
        "filters": {"product": "Cortex, Prisma Cloud, SASE"},
        "expected_keywords": ["cortex", "prisma", "security"]
    },
    {
        "query": "hashicorp vault workshop",
        "filters": {"vendor": "hashicorp"},
        "expected_keywords": ["vault", "workshop", "webinar"]
    },
    {
        "query": "terraform cloud migration",
        "filters": {"product": "vault, terraform, boundary, consul, nomad, packer, waypoint, sentinel, terraform cloud"},
        "expected_keywords": ["terraform", "cloud", "migration"]
    },
    {
        "query": "webinar event",
        "filters": {"type": "announcement, event, webinar, product update"},
        "expected_keywords": ["webinar", "event"]
    }
]

def evaluate_search():
    results = {}
    
    # First try with no filters to see if basic search works
    logging.info("Testing basic search without filters")
    basic_results = {}
    
    for case in test_cases:
        # Try vector search
        vector_results = hybrid_search(case["query"], None, top_k=5)
        
        basic_results[case["query"]] = {
            "vector_count": len(vector_results["documents"]),
            "vector_first_doc": vector_results["documents"][0][:100] if vector_results["documents"] else "No results"
        }
    
    # Now test with filters
    logging.info("Testing search with filters")
    for case in test_cases:
        search_results = hybrid_search(
            case["query"], 
            case["filters"], 
            top_k=5
        )
        
        # Check if results contain expected keywords
        keyword_matches = []
        for doc in search_results["documents"]:
            matches = [kw for kw in case["expected_keywords"] if kw.lower() in doc.lower()]
            keyword_matches.extend(matches)
        
        # Calculate keyword coverage
        unique_matches = set(keyword_matches)
        coverage = len(unique_matches) / len(case["expected_keywords"]) if case["expected_keywords"] else 0
        
        results[case["query"]] = {
            "coverage": coverage,
            "matched_keywords": list(unique_matches),
            "missing_keywords": [kw for kw in case["expected_keywords"] if kw.lower() not in unique_matches],
            "result_count": len(search_results["documents"]),
            "first_result": search_results["documents"][0][:100] if search_results["documents"] else "No results"
        }
    
    # Save results
    os.makedirs("data/eval", exist_ok=True)
    
    with open("data/eval/basic_search_results.json", "w") as f:
        json.dump(basic_results, f, indent=2)
        
    with open("data/eval/search_quality.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return {"basic": basic_results, "filtered": results}

if __name__ == "__main__":
    results = evaluate_search()
    
    print("\nBASIC SEARCH RESULTS (no filters):")
    print(json.dumps(results["basic"], indent=2))
    
    print("\nFILTERED SEARCH RESULTS:")
    print(json.dumps(results["filtered"], indent=2))