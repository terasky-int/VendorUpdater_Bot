#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.llm_utils import get_chroma_collection

def test_chromadb_connection():
    """Test connection to remote ChromaDB and check document count"""
    try:
        print("🔍 Testing ChromaDB connection...")
        
        # Get collection
        collection = get_chroma_collection()
        print(f"✅ Successfully connected to collection: {collection.name}")
        
        # Get document count
        count = collection.count()
        print(f"📊 Total documents in collection: {count}")
        
        # Try to peek at some data
        if count > 0:
            results = collection.peek(limit=30)
            print(f"📋 Sample documents:")
            for i, doc_id in enumerate(results['ids']):
                print(f"  {i+1}. ID: {doc_id}")
                if results['metadatas'] and i < len(results['metadatas']):
                    metadata = results['metadatas'][i]
                    print(f"     Vendor: {metadata.get('vendor', 'N/A')}")
                    print(f"     Type: {metadata.get('type', 'N/A')}")
                    print(f"     Date: {metadata.get('date', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_chromadb_connection()
    sys.exit(0 if success else 1)