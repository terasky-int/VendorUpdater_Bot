"""
Test script for the RAG API
"""

import sys
import os
import requests
import json

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_api(query, filters=None):
    """
    Test the RAG API with a query and optional filters
    
    Args:
        query: The query text
        filters: Optional metadata filters
    """
    url = "http://localhost:8000/query"
    payload = {
        "query": query,
        "metadata_filters": filters,
        "top_k": 5
    }
    
    print(f"\n--- Testing query: '{query}' ---")
    if filters:
        print(f"Filters: {filters}")
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Answer: {result['answer']}")
        print(f"Sources: {len(result['sources'])}")
        
        # Print first source
        if result['sources']:
            print("\nFirst source:")
            print(f"Text: {result['sources'][0]['text']}")
            print(f"Metadata: {result['sources'][0]['metadata']}")
        
        return result
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    # Basic test cases
    test_api("test query")
    test_api("Show me webinars from the past week", {"type": "webinar"})
    test_api("What's new from hashicorp about terraform", {"vendor": "hashicorp", "product": "terraform"})
    test_api("Recent security updates", {"type": "security"})
    
    # Additional test cases
    test_api("HashiCorp Vault features", {"vendor": "hashicorp", "product": "vault"})
    test_api("Palo Alto Networks certification", {"vendor": "paloaltonetworks"})
    test_api("Cloud migration case studies", {})
    
    # Test with partial product name
    test_api("What's new in Terra", {"product": "terra"})
    
    # Test with multiple type filters
    test_api("Recent announcements and events", {"type": "announcement"})