import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.llm_utils import load_config
from chromadb import PersistentClient, HttpClient


if __name__ == "__main__":
    config = load_config()
    
    # Use same client configuration as main app
    use_remote = config["vector_store"].get("use_remote", False)
    
    if use_remote:
        chroma_host = config["vector_store"].get("remote_host")
        chroma_port = config["vector_store"].get("remote_port", 8000)
        client = HttpClient(host=chroma_host, port=chroma_port)
    else:
        chroma_path = config["vector_store"].get("persist_directory", "data/chroma")
        client = PersistentClient(path=chroma_path)
    
    # Get all collections
    collections = client.list_collections()
    
    print(f"Number of collections: {len(collections)}")
    print("\nCollection details:")
    
    for collection in collections:
        data = collection.get()
        doc_count = len(data['ids'])
        print(f"\n- {collection.name}: {doc_count} documents")
        
        if doc_count > 0:
            print("  Document IDs:")
            for doc_id in data['ids']:
                print(f"    • {doc_id}")
        else:
            print("    (no documents)")
