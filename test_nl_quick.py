"""
Quick test for enhanced natural language query processing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_nl_processing():
    """Test basic NL processing without database dependencies"""
    from src.nl_query_processor import NLQueryProcessor
    
    processor = NLQueryProcessor()
    
    test_queries = [
        "Show me recent security alerts from HashiCorp",
        "How many emails from Palo Alto in the past week?",
        "List all vendors",
        "Find Terraform updates",
        "Show AWS Bedrock announcements"
    ]
    
    print("🧪 Testing Enhanced Natural Language Processing\n")
    
    for query in test_queries:
        print(f"Query: {query}")
        processed = processor.process_query(query)
        
        print(f"  ✓ Intent: {processed['intent']}")
        print(f"  ✓ Vendor: {processed['filters']['vendor'] or 'None'}")
        print(f"  ✓ Product: {processed['filters']['product'] or 'None'}")
        print(f"  ✓ Type: {processed['filters']['type'] or 'None'}")
        print(f"  ✓ Time Filter: {processed['time_filter'] or 'None'}")
        print(f"  ✓ Search Terms: '{processed['search_terms']}'")
        print()

if __name__ == "__main__":
    test_basic_nl_processing()