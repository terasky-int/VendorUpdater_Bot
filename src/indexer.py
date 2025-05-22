import logging
from chromadb import PersistentClient
import llm_utils
from llm_utils import load_config, get_chroma_collection

def index_documents(texts, metadatas, ids, embeddings):
    collection = get_chroma_collection()

    collection.add(
        documents=texts,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings
    )

    logging.info(f"✅ Indexed {len(texts)} documents into the vector store")

if __name__ == "__main__":
    import random

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

    # Titan expects 1024-dim embeddings; we'll fake them for now
    test_embeddings = [[random.uniform(-1, 1) for _ in range(1024)] for _ in range(2)]

    index_documents(
        texts=test_texts,
        metadatas=test_metadata,
        ids=test_ids,
        embeddings=test_embeddings
    )

    print("✅ Test documents indexed. You can now search for '#synthetic-test' to verify.")