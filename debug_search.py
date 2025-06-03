from src import llm_utils
import json

def inspect_chroma_collection():
    """Check what's actually in the ChromaDB collection"""
    collection = llm_utils.get_chroma_collection()
    
    # Get collection info
    count = collection.count()
    print(f"Total documents in collection: {count}")
    
    if count == 0:
        print("Collection is empty. No documents to search.")
        return
    
    # Get a sample of documents
    try:
        sample = collection.get(limit=5)
        print("\nSample documents:")
        for i, (doc, meta) in enumerate(zip(sample["documents"], sample["metadatas"])):
            print(f"\nDocument {i+1}:")
            print(f"ID: {sample['ids'][i]}")
            print(f"Metadata: {json.dumps(meta, indent=2)}")
            print(f"Text snippet: {doc[:100]}...")
    except Exception as e:
        print(f"Error getting sample: {e}")
    
    # List all unique metadata values
    try:
        all_data = collection.get()
        vendors = set(m.get("vendor", "unknown") for m in all_data["metadatas"])
        products = set(m.get("product", "unknown") for m in all_data["metadatas"])
        types = set(m.get("type", "unknown") for m in all_data["metadatas"])
        
        print("\nUnique metadata values:")
        print(f"Vendors: {vendors}")
        print(f"Products: {products}")
        print(f"Types: {types}")
    except Exception as e:
        print(f"Error analyzing metadata: {e}")

def test_basic_search():
    """Test a basic search without filters"""
    collection = llm_utils.get_chroma_collection()
    
    # Test queries that match our actual data
    test_queries = ["palo alto certification", "google cloud", "hashicorp vault", "terraform cloud"]
    
    for query in test_queries:
        embedding = llm_utils.embed_text_titan(query)
        
        print(f"\nTesting basic search for '{query}'")
        try:
            results = collection.query(
                query_embeddings=[embedding],
                n_results=3
            )
            
            if results["documents"] and results["documents"][0]:
                print(f"Found {len(results['documents'][0])} results")
                for i, doc in enumerate(results["documents"][0]):
                    print(f"\nResult {i+1}:")
                    print(f"Text: {doc[:100]}...")
                    print(f"Metadata: {results['metadatas'][0][i]}")
            else:
                print("No results found for basic search")
        except Exception as e:
            print(f"Error in basic search: {e}")

if __name__ == "__main__":
    print("=== ChromaDB Collection Inspection ===")
    inspect_chroma_collection()
    
    print("\n=== Basic Search Test ===")
    test_basic_search()