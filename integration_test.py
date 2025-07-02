#!/usr/bin/env python3
"""Integration test between vendor_updater_bot and TeraskyRag"""

import os
import sys
import logging
import time
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_integration():
    """Test integration between vendor_updater_bot and TeraskyRag"""
    test_id = str(uuid.uuid4())[:8]
    logging.info(f"Starting integration test with ID: {test_id}")
    
    # Step 1: Test vendor_updater_bot configuration
    logging.info("Step 1: Testing vendor_updater_bot configuration")
    try:
        os.chdir("vendor_updater_bot")
        sys.path.insert(0, os.path.abspath("."))
        
        from src.llm_utils import load_config
        config = load_config()
        logging.info("✅ vendor_updater_bot configuration loaded successfully")
        
        # Check ChromaDB connection
        from src.llm_utils import get_chroma_collection
        collection = get_chroma_collection()
        initial_count = collection.count()
        logging.info(f"✅ ChromaDB connection successful, initial document count: {initial_count}")
        
        # Reset path for next step
        sys.path.pop(0)
        os.chdir("..")
    except Exception as e:
        logging.error(f"❌ vendor_updater_bot test failed: {e}")
        return False
    
    # Step 2: Test TeraskyRag configuration
    logging.info("Step 2: Testing TeraskyRag configuration")
    try:
        os.chdir("TeraskyRag")
        sys.path.insert(0, os.path.abspath("."))
        
        from src.llm_utils import load_config
        config = load_config()
        logging.info("✅ TeraskyRag configuration loaded successfully")
        
        # Check ChromaDB connection (should be same as vendor_updater_bot)
        from src.llm_utils import get_chroma_collection
        collection = get_chroma_collection()
        rag_count = collection.count()
        logging.info(f"✅ TeraskyRag ChromaDB connection successful, document count: {rag_count}")
        
        # Verify counts match
        assert initial_count == rag_count, f"Document counts don't match: {initial_count} vs {rag_count}"
        logging.info("✅ Document counts match between systems")
        
        # Reset path for next step
        sys.path.pop(0)
        os.chdir("..")
    except Exception as e:
        logging.error(f"❌ TeraskyRag test failed: {e}")
        return False
    
    # Step 3: Test data flow (simulated)
    logging.info("Step 3: Testing data flow between systems")
    try:
        # Create test document in vendor_updater_bot
        test_doc = f"Integration test document {test_id} created at {datetime.now().isoformat()}"
        test_metadata = {
            "vendor": "test_vendor",
            "product": "test_product",
            "type": "test",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "email_id": f"test_{test_id}",
            "integration_test": True
        }
        
        # Add document to ChromaDB through vendor_updater_bot
        os.chdir("vendor_updater_bot")
        sys.path.insert(0, os.path.abspath("."))
        
        from src.llm_utils import get_chroma_collection
        collection = get_chroma_collection()
        
        # Generate embedding
        from src.embedder import embed_text
        embedding = embed_text(test_doc)
        
        # Add to ChromaDB
        collection.add(
            documents=[test_doc],
            metadatas=[test_metadata],
            ids=[f"test_{test_id}"],
            embeddings=[embedding]
        )
        logging.info(f"✅ Test document added to ChromaDB through vendor_updater_bot")
        
        # Reset path for next step
        sys.path.pop(0)
        os.chdir("..")
        
        # Verify document is accessible from TeraskyRag
        os.chdir("TeraskyRag")
        sys.path.insert(0, os.path.abspath("."))
        
        from src.llm_utils import get_chroma_collection
        collection = get_chroma_collection()
        
        # Query for the test document
        results = collection.get(
            where={"integration_test": True, "email_id": f"test_{test_id}"}
        )
        
        assert len(results["documents"]) > 0, "Test document not found in TeraskyRag"
        assert results["documents"][0] == test_doc, "Document content doesn't match"
        logging.info("✅ Test document successfully retrieved through TeraskyRag")
        
        # Clean up test document
        collection.delete(ids=[f"test_{test_id}"])
        logging.info("✅ Test document cleaned up")
        
        # Reset path
        sys.path.pop(0)
        os.chdir("..")
    except Exception as e:
        logging.error(f"❌ Data flow test failed: {e}")
        return False
    
    logging.info("✅ All integration tests passed successfully!")
    return True

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)