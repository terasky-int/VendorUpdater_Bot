import os
import json
import logging
from chromadb import PersistentClient
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from src import llm_utils
# from llm_utils import load_config, embed_text_titan

# Load configuration
def load_config(path="config/config.yaml"):
    return llm_utils.load_config(path)

def print_all_documents(collection):
    print("\n🗌 Dumping all metadata from the vector store...")
    try:
        all_data = collection.get()
        count = len(all_data.get("documents", []))
        print(f"\n📦 Total Documents Stored: {count}")
        for i, meta in enumerate(all_data.get("metadatas", [])):
            print(f"\n#{i+1} Metadata:")
            print(json.dumps(meta, indent=2))
    except Exception as e:
        logging.error(f"Failed to dump all documents: {e}")
        print("❌ Could not retrieve vector store contents.")

def search_query():
    collection = llm_utils.get_chroma_collection()  

    print_all_documents(collection)

    print("\nEnter your search query (or type 'exit' to quit):")
    while True:
        query = input("🔍 Query: ")
        if query.lower() == "exit":
            break

        vendor = input("🔎 Filter by vendor (leave blank for any): ").strip()
        product = input("🔎 Filter by product (leave blank for any): ").strip()
        doc_type = input("🔎 Filter by type (leave blank for any): ").strip()
        date_limit = input("🕓 Max date (YYYY-MM-DD, leave blank to ignore): ").strip()

        filters = []
        if vendor:
            filters.append({"vendor": vendor})
        if product:
            filters.append({"product": product})
        if doc_type:
            filters.append({"type": doc_type})
        if date_limit:
            filters.append({"date": {"$lte": date_limit}})

        chroma_where = filters[0] if len(filters) == 1 else {"$and": filters} if filters else None

        try:
            embedding = llm_utils.embed_text_titan(query)
            results = collection.query(
                query_embeddings=[embedding],
                n_results=5,
                where=chroma_where
            )

            total_matches = len(results["documents"][0])
            print(f"\n🔎 Total Matches Found: {total_matches}")

            print("\n🔎 Top Results:")
            for i, doc in enumerate(results["documents"][0]):
                print(f"\n#{i+1} ---------------------------")
                print(doc[:500] + ("..." if len(doc) > 500 else ""))
                print("Metadata:", results["metadatas"][0][i])

            os.makedirs("logs", exist_ok=True)
            with open("logs/debug_search_output.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logging.error(f"Search failed: {e}")
            print("❌ Failed to execute query. Check logs.")

def query(query_text, top_k=3, filters=None):
    collection = llm_utils.get_chroma_collection()

    if filters:
        chroma_where = filters[0] if len(filters) == 1 else {"$and": filters}
    else:
        chroma_where = None

    embedding = llm_utils.embed_text_titan(query_text)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=chroma_where
    )
    return results


def search_by_vector(query_text, top_k=3, filters=None):
    """Search by vector embedding with optional filters"""
    try:
        collection = llm_utils.get_chroma_collection()
        
        # Process filters if provided
        chroma_where = None
        if filters:
            if isinstance(filters, dict):
                chroma_where = filters
            elif isinstance(filters, list):
                chroma_where = filters[0] if len(filters) == 1 else {"$and": filters}
        
        # Generate embedding and search
        embedding = llm_utils.embed_text_titan(query_text)
        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=chroma_where
        )
        
        return results
    except Exception as e:
        logging.error(f"Vector search failed: {e}")
        raise


if __name__ == "__main__":
    search_query()