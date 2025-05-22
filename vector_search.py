import os
import json
import logging
import boto3
from chromadb import PersistentClient
from typing import List


def load_config():
    import yaml
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)


def embed_with_titan(text: str) -> List[float]:
    bedrock_client = boto3.client("bedrock-runtime", region_name="eu-west-1")
    try:
        response = bedrock_client.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps({"inputText": text}),
            contentType="application/json",
            accept="application/json"
        )
        body = json.loads(response["body"].read().decode("utf-8"))
        return body["embedding"]
    except Exception as e:
        logging.error(f"Embedding failed for text: {text[:100]}... — {str(e)}")
        raise


def print_all_documents(collection):
    print("\n📋 Dumping all metadata from the vector store...")
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
    config = load_config()
    chroma_path = config["vector_store"].get("persist_directory", "data/chroma")
    collection_name = config["vector_store"].get("collection_name", "vendor_emails")

    client = PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(name=collection_name)

    # Debug mode: show everything in DB once
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

        # Build metadata filter
        filters = []
        if vendor:
            filters.append({"vendor": vendor})
        if product:
            filters.append({"product": product})
        if doc_type:
            filters.append({"type": doc_type})
        if date_limit:
            filters.append({"date": {"$lte": date_limit}})

        chroma_where = None
        if len(filters) == 1:
            chroma_where = filters[0]
        elif len(filters) > 1:
            chroma_where = {"$and": filters}

        try:
            embedding = embed_with_titan(query)
            results = collection.query(
                query_embeddings=[embedding],
                n_results=5,
                where=chroma_where if chroma_where else None
            )

            total_matches = len(results["documents"][0])
            print(f"\n🔎 Total Matches Found: {total_matches}")

            print("\n🔎 Top Results:")
            for i, doc in enumerate(results["documents"][0]):
                print(f"\n#{i+1} ---------------------------")
                print(doc[:500] + ("..." if len(doc) > 500 else ""))
                print("Metadata:", results["metadatas"][0][i])

            # Save full results to logs
            os.makedirs("logs", exist_ok=True)
            with open("logs/debug_search_output.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logging.error(f"Search failed: {e}")
            print("❌ Failed to execute query. Check logs.")


if __name__ == "__main__":
    search_query()
