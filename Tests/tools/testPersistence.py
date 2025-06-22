import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.llm_utils import load_config
from chromadb import HttpClient

def test_persistence():
    config = load_config()
    
    chroma_host = config["vector_store"].get("remote_host")
    chroma_port = config["vector_store"].get("remote_port", 8000)
    client = HttpClient(host=chroma_host, port=chroma_port)
    
    test_collection_name = "persistence_test"
    test_doc_id = f"test_doc_{int(time.time())}"
    
    # Step 1: Add test document
    collection = client.get_or_create_collection(test_collection_name)
    collection.add(
        documents=[f"Test document created at {time.ctime()}"],
        ids=[test_doc_id]
    )
    
    print(f"✅ Added test document: {test_doc_id}")
    print("Now restart your ChromaDB container and run this script again to check persistence")
    
    # Step 2: Check existing test documents
    data = collection.get()
    if data['ids']:
        print(f"\n📋 Found {len(data['ids'])} test documents:")
        for doc_id in data['ids']:
            print(f"   • {doc_id}")
    else:
        print("\n❌ No test documents found")

if __name__ == "__main__":
    test_persistence()