#!/usr/bin/env python3
"""Basic functionality test for vendor_updater_bot"""

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
        assert "email" in config, "Missing email section in config"
        assert "vector_store" in config, "Missing vector_store section in config"
        
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

def test_embedding_generation():
    """Test if embedding generation works"""
    try:
        from src.embedder import embed_text
        
        test_text = "This is a test document for embedding generation"
        embedding = embed_text(test_text)
        
        assert embedding is not None, "Embedding is None"
        assert len(embedding) > 0, "Embedding is empty"
        
        logging.info(f"✅ Embedding generation successful, dimension: {len(embedding)}")
        return True
    except Exception as e:
        logging.error(f"❌ Embedding generation failed: {e}")
        return False

def run_all_tests():
    """Run all tests and return overall status"""
    results = {
        "config_loading": test_config_loading(),
        "chroma_connection": test_chroma_connection(),
        "embedding_generation": test_embedding_generation()
    }
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    logging.info(f"Test Results: {success_count}/{total_count} tests passed")
    
    return all(results.values())

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)