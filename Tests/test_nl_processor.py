"""
Test script for Natural Language Query Processing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nl_query_processor import process_natural_language_query, NLQueryProcessor
import json

def test_nl_queries():
    """Test various natural language queries"""
    
    test_queries = [
        "Show me recent security alerts from HashiCorp",
        "How many emails from Palo Alto in the past week?",
        "Find Terraform updates from last month",
        "List all vendors",
        "What products does HashiCorp offer?",
        "Show me recent Vault vulnerabilities",
        "Count security emails from the past 30 days",
        "Find AWS Bedrock announcements",
        "Show latest marketing emails",
        "Get Prisma Cloud security updates"
    ]
    
    processor = NLQueryProcessor()
    
    print("🧪 Testing Natural Language Query Processing\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: {query}")
        
        # Test the processor
        processed = processor.process_query(query)
        
        print(f"  Intent: {processed['intent']}")
        print(f"  Search Terms: '{processed['search_terms']}'")
        print(f"  Vendor: {processed['filters']['vendor']}")
        print(f"  Product: {processed['filters']['product']}")
        print(f"  Type: {processed['filters']['type']}")
        print(f"  Time Filter: {processed['time_filter']} days" if processed['time_filter'] else "  Time Filter: None")
        print()

def test_full_processing():
    """Test full query processing with responses"""
    
    test_queries = [
        "How many emails from HashiCorp?",
        "List all vendors",
        "Show recent security alerts"
    ]
    
    print("🔍 Testing Full Query Processing\n")
    
    for query in test_queries:
        print(f"Query: {query}")
        try:
            result = process_natural_language_query(query)
            print(f"  Answer: {result['answer']}")
            print(f"  Intent: {result['intent']}")
        except Exception as e:
            print(f"  Error: {e}")
        print()

if __name__ == "__main__":
    test_nl_queries()
    print("-" * 50)
    test_full_processing()