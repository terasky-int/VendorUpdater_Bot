import logging
import random
from chromadb import PersistentClient
from src import llm_utils

def reset_chroma_db():
    """Reset the ChromaDB collection by deleting and recreating it"""
    try:
        config = llm_utils.load_config()
        collection_name = config["vector_store"].get("collection_name", "vendor_emails")
        
        # Check if we should use remote ChromaDB
        use_remote = config["vector_store"].get("use_remote", False)
        
        if use_remote:
            from chromadb import HttpClient
            chroma_host = config["vector_store"].get("remote_host")
            chroma_port = config["vector_store"].get("remote_port", 8000)
            client = HttpClient(host=chroma_host, port=chroma_port)
        else:
            chroma_path = config["vector_store"].get("persist_directory", "data/chroma")
            client = PersistentClient(path=chroma_path)
        
        # Delete existing collection if it exists
        try:
            client.delete_collection(name=collection_name)
            logging.info(f"Deleted existing collection: {collection_name}")
        except Exception:
            logging.info(f"Collection {collection_name} didn't exist, creating new one")
        
        # Create new collection
        collection = client.create_collection(name=collection_name)
        logging.info(f"Created new collection: {collection_name}")
        return collection
        
    except Exception as e:
        logging.error(f"Failed to reset ChromaDB: {e}")
        raise

def index_documents(texts, metadatas, ids, embeddings):
    try:
        assert len(texts) == len(metadatas) == len(ids) == len(embeddings), \
            "All input lists (texts, metadatas, ids, embeddings) must have the same length"

        # Normalize metadata - ChromaDB doesn't accept None values
        required_fields = ["vendor", "product", "type", "date"]
        optional_date_fields = ["event_date", "registration_deadline", "expiration_date"]
        
        for m in metadatas:
            for field in required_fields:
                m.setdefault(field, "unknown")
            # Convert None values to empty strings for ChromaDB compatibility
            for field in optional_date_fields:
                if field in m and m[field] is None:
                    m[field] = ""
                elif field not in m:
                    m[field] = ""

        collection = llm_utils.get_chroma_collection()

        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )

        logging.info(f"✅ Indexed {len(texts)} documents into the vector store")

    except Exception as e:
        logging.error(f"❌ Failed to index documents: {e}")
        logging.debug(f"texts: {texts}")
        logging.debug(f"ids: {ids}")
        logging.debug(f"metadatas: {metadatas}")
        logging.debug(f"embeddings count: {len(embeddings)}")
        raise

def index(chunks, raw_embeddings, metadatas, config=None):
    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    # vectors = [e["embedding"] for e in raw_embeddings]  # extract only the vectors
    vectors = raw_embeddings

    if not isinstance(vectors[0], list):
        raise TypeError("Expected raw_embeddings to be a list of float lists (embeddings)")
    
    index_documents(
        texts=texts,
        metadatas=metadatas,
        ids=ids,
        embeddings=vectors
    )

if __name__ == "__main__":
    # Reset ChromaDB collection to fix dimension issues
    print("🔄 Resetting ChromaDB collection...")
    reset_chroma_db()
    
    test_texts = [
        "Join our upcoming Terraform webinar on infrastructure automation. #synthetic-test",
        "A new vulnerability was found in IBM Cloud Pak — patch it today. #synthetic-test"
    ]

    test_metadata = [
        {
            "vendor": "hashicorp",
            "product": "terraform",
            "type": "webinar",
            "date": "2025-04-10"
        },
        {
            "vendor": "ibm",
            "product": "cloud pak",
            "type": "vulnerability",
            "date": "2025-05-01"
        }
    ]

    test_ids = ["test-doc-001", "test-doc-002"]
    # Generate embeddings with correct dimension (1024 for Titan)
    test_embeddings = [[random.uniform(-1, 1) for _ in range(1024)] for _ in range(2)]

    index_documents(
        texts=test_texts,
        metadatas=test_metadata,
        ids=test_ids,
        embeddings=test_embeddings
    )

    print("✅ Test documents indexed. Running verification search...")

    # Verification query using proper embeddings
    try:
        collection = llm_utils.get_chroma_collection()
        query_embedding = [random.uniform(-1, 1) for _ in range(1024)]
        results = collection.query(query_embeddings=[query_embedding], n_results=2)
        print("🔍 Search Results:")
        if results["documents"] and results["documents"][0]:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                print(f"- {doc[:50]}... | {meta}")
        else:
            print("No results found")
    except Exception as e:
        print(f"❌ Query failed: {e}")