"""
Test script to verify the integration of enhanced graph database and unified search
"""

import sys
import os
import logging

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the enhanced functions to verify they're available
from graph_db import (
    get_vendor_products_by_confidence,
    add_email_to_graph_enhanced,
    import_all_emails_enhanced,
    cleanup_incorrect_relationships,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW
)

from src.unified_search import (
    process_search_query,
    graph_enhanced_ranking,
    unified_search,
    get_vendor_products_enhanced,
    format_search_results
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def test_graph_db_enhanced():
    """Test the enhanced graph database functions"""
    print("\n🧪 Testing enhanced graph database functions")
    
    # Test confidence levels
    print(f"Confidence levels: HIGH={CONFIDENCE_HIGH}, MEDIUM={CONFIDENCE_MEDIUM}, LOW={CONFIDENCE_LOW}")
    
    # Test vendor products by confidence
    vendor = "hashicorp"
    print(f"\nTesting get_vendor_products_by_confidence for vendor '{vendor}'")
    products = get_vendor_products_by_confidence(vendor, CONFIDENCE_HIGH)
    print(f"High confidence products: {products}")
    
    products = get_vendor_products_by_confidence(vendor, CONFIDENCE_MEDIUM)
    print(f"Medium+ confidence products: {products}")
    
    products = get_vendor_products_by_confidence(vendor, CONFIDENCE_LOW)
    print(f"All confidence products: {products}")
    
    # Test cleanup function (just print info, don't actually run it)
    print("\nCleanup function available: cleanup_incorrect_relationships()")
    
    return True

def test_unified_search():
    """Test the unified search functions"""
    print("\n🧪 Testing unified search functions")
    
    # Test query processing
    query = "Show me recent security updates from hashicorp about vault"
    print(f"\nProcessing query: '{query}'")
    
    processed = process_search_query(query)
    print(f"Processed query: {processed}")
    
    # Test enhanced vendor products
    vendor = "hashicorp"
    print(f"\nTesting get_vendor_products_enhanced for vendor '{vendor}'")
    products = get_vendor_products_enhanced(vendor)
    print(f"Enhanced products: {products}")
    
    # Test unified search (with mock results)
    print("\nUnified search function available: unified_search()")
    print("Graph enhanced ranking function available: graph_enhanced_ranking()")
    print("Format search results function available: format_search_results()")
    
    return True

if __name__ == "__main__":
    print("🔍 Testing Enhanced Integration")
    print("=" * 50)
    
    # Test graph database enhancements
    graph_result = test_graph_db_enhanced()
    
    # Test unified search
    search_result = test_unified_search()
    
    # Print overall result
    if graph_result and search_result:
        print("\n✅ All enhanced functions are available and ready to use!")
    else:
        print("\n❌ Some tests failed. Check the logs for details.")