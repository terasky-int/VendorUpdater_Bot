import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.llm_utils import load_config
from chromadb import HttpClient

if __name__ == "__main__":
    config = load_config()
    
    chroma_host = config["vector_store"].get("remote_host")
    chroma_port = config["vector_store"].get("remote_port", 8000)
    client = HttpClient(host=chroma_host, port=chroma_port)
    
    # Create test collection
    collection = client.get_or_create_collection("test_persistence")
    
    # Add test document
    collection.add(
        documents=["This is a test document for persistence"],
        ids=["test_doc_1"]
    )
    
    print("Test document added. Restart ChromaDB and run testChromaDB.py to check persistence.")