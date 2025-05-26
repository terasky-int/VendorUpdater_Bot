
import logging
import random
from chromadb import PersistentClient
from src import llm_utils

def index_documents(texts, metadatas, ids, embeddings):
    try:
        assert len(texts) == len(metadatas) == len(ids) == len(embeddings), \
            "All input lists (texts, metadatas, ids, embeddings) must have the same length"

        # Normalize metadata
        required_fields = ["vendor", "product", "type", "date"]
        for m in metadatas:
            for field in required_fields:
                m.setdefault(field, "unknown")

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
    test_embeddings = [[random.uniform(-1, 1) for _ in range(1024)] for _ in range(2)]

    index_documents(
        texts=test_texts,
        metadatas=test_metadata,
        ids=test_ids,
        embeddings=test_embeddings
    )

    print("✅ Test documents indexed. Running verification search...")

    # Verification query
    try:
        collection = llm_utils.get_chroma_collection()
        results = collection.query(query_texts=["#synthetic-test"], n_results=2)
        print("🔍 Search Results:")
        for doc, meta in zip(results["documents"], results["metadatas"]):
            print(f"- {doc[0]} | {meta}")
    except Exception as e:
        print(f"❌ Query failed: {e}")


# import logging
# from chromadb import PersistentClient
# from src import llm_utils
# # from llm_utils import load_config, get_chroma_collection

# def index_documents(texts, metadatas, ids, embeddings):
#     try:
#         collection = llm_utils.get_chroma_collection()

#         collection.add(
#             documents=texts,
#             metadatas=metadatas,
#             ids=ids,
#             embeddings=embeddings
#         )

#         logging.info(f"✅ Indexed {len(texts)} documents into the vector store")

#     except Exception as e:
#         logging.error(f"❌ Failed to index documents: {e}")
#         logging.debug(f"texts: {texts}")
#         logging.debug(f"ids: {ids}")
#         logging.debug(f"metadatas: {metadatas}")
#         logging.debug(f"embeddings: (len={len(embeddings)})")
#         raise

# def index(chunks, embeddings, metadatas, config=None):
#     texts = [c["text"] for c in chunks]
#     ids = [c["id"] for c in chunks]

#     index_documents(
#         texts=texts,
#         metadatas=metadatas,
#         ids=ids,
#         embeddings=embeddings
#     )

# if __name__ == "__main__":
#     import random

#     test_texts = [
#         "Join our upcoming Terraform webinar on infrastructure automation. #synthetic-test",
#         "A new vulnerability was found in IBM Cloud Pak — patch it today. #synthetic-test"
#     ]

#     test_metadata = [
#         {
#             "vendor": "hashicorp",
#             "product": "terraform",
#             "type": "webinar",
#             "date": "2025-04-10"
#         },
#         {
#             "vendor": "ibm",
#             "product": "cloud pak",
#             "type": "vulnerability",
#             "date": "2025-05-01"
#         }
#     ]

#     test_ids = ["test-doc-001", "test-doc-002"]

#     # Titan expects 1024-dim embeddings; we'll fake them for now
#     test_embeddings = [[random.uniform(-1, 1) for _ in range(1024)] for _ in range(2)]

#     index_documents(
#         texts=test_texts,
#         metadatas=test_metadata,
#         ids=test_ids,
#         embeddings=test_embeddings
#     )

#     print("✅ Test documents indexed. You can now search for '#synthetic-test' to verify.")

#     collection = llm_utils.get_chroma_collection()
#     results = collection.query(query_texts=["#synthetic-test"], n_results=2)
#     print("🔍 Search Results:", results)