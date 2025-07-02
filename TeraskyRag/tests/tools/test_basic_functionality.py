#!/usr/bin/env python3
"""Basic functionality test for TeraskyRag"""

import os
import sys
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_config_loading():
    """Test if configuration can be loaded"""
    try:
        from src.llm_utils import load_config
        config = load_config()
        logging.info("✅ Configuration loaded successfully")
        
        # Check essential config sections
        assert "vector_store" in config, "Missing vector_store section in config"
        assert "neo4j" in config, "Missing neo4j section in config"
        assert "rag" in config, "Missing rag section in config"
        
        logging.info(f"✅ Config contains {len(config)} sections")
        return True
    except Exception as e:
        logging.error(f"❌ Configuration loading failed: {e}")
        return False

def test_chroma_connection():
    """Test if ChromaDB connection works"""
    try:
        from src.llm_utils import get_chroma_collection
        collection = get_chroma_collection()
        count = collection.count()
        logging.info(f"✅ ChromaDB connection successful, collection has {count} documents")
        return True
    except Exception as e:
        logging.error(f"❌ ChromaDB connection failed: {e}")
        return False

def test_vector_search():
    """Test if vector search works"""
    try:
        from src.vector_search import search_by_vector
        
        test_query = "hashicorp vault"
        results = search_by_vector(test_query, top_k=3)
        
        assert results is not None, "Search results are None"
        
        logging.info(f"✅ Vector search successful, found {len(results['documents'])} results")
        return True
    except Exception as e:
        logging.error(f"❌ Vector search failed: {e}")
        return False

def run_all_tests():
    """Run all tests and return overall status"""
    results = {
        "config_loading": test_config_loading(),
        "chroma_connection": test_chroma_connection(),
        "vector_search": test_vector_search()
    }
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    logging.info(f"Test Results: {success_count}/{total_count} tests passed")
    
    return all(results.values())

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)