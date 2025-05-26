import logging
import boto3
import json
from typing import List


def embed_chunks(chunks: List[dict], config: dict) -> List[List[float]]:
    model_id = config["embedding"]["model"]
    client = boto3.client("bedrock-runtime")

    embeddings = []
    dim_check = None

    for chunk in chunks:
        body = {
            "inputText": chunk["text"]
        }

        try:
            response = client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )

            result = json.loads(response["body"].read())
            vector = result["embedding"]

            if dim_check is None:
                dim_check = len(vector)
                logging.info(f"✅ Consistent embedding dimension: {dim_check}")
            elif len(vector) != dim_check:
                logging.warning(f"⚠️ Inconsistent embedding size: expected {dim_check}, got {len(vector)}")

            embeddings.append(vector)
            logging.debug(f"Embedded chunk {chunk['chunk_id']}")

        except Exception as e:
            logging.error(f"Embedding failed for chunk {chunk['chunk_id']}: {e}")
            embeddings.append([])

    return embeddings


if __name__ == "__main__":
    import os

    logging.basicConfig(level=logging.DEBUG)
    
    test_config = {
        "embedding": {
            "model": "amazon.titan-embed-text-v2:0"
        }
    }

    test_chunks = [
        {"chunk_id": "chunk-0", "text": "Hello world", "position": 0},
        {"chunk_id": "chunk-1", "text": "Embedding test sentence", "position": 1},
    ]

    vectors = embed_chunks(test_chunks, test_config)

    print(f"\n✅ Got {len(vectors)} embeddings, each of dimension {len(vectors[0]) if vectors else 0}")


# import logging
# import boto3
# import json
# from typing import List

# def embed_chunks(chunks: List[dict], config: dict) -> List[dict]:
#     model_id = config["embedding"]["model"]
#     client = boto3.client("bedrock-runtime")

#     embeddings = []
#     for chunk in chunks:
#         body = {
#             "inputText": chunk["text"]
#         }

#         try:
#             response = client.invoke_model(
#                 modelId=model_id,
#                 contentType="application/json",
#                 accept="application/json",
#                 body=json.dumps(body)
#             )

#             result = json.loads(response["body"].read())
#             vector = result["embedding"]

#             # Log dimension once
#             if not embeddings:
#                 logging.info(f"🔢 Detected embedding dimension: {len(vector)} (from model {model_id})")

#             embeddings.append({
#                 "chunk_id": chunk["chunk_id"],
#                 "embedding": vector,
#                 "position": chunk["position"]
#             })
#             logging.debug(f"Embedded chunk {chunk['chunk_id']}")
#             dims = set(len(e["embedding"]) for e in embeddings if e["embedding"])
#             if len(dims) > 1:
#                 logging.warning(f"⚠️ Multiple embedding dimensions found: {dims}")
#             elif dims:
#                 logging.info(f"✅ Consistent embedding dimension: {list(dims)[0]}")

#         except Exception as e:
#             logging.error(f"Embedding failed for chunk {chunk['chunk_id']}: {e}")
#             embeddings.append({
#                 "chunk_id": chunk["chunk_id"],
#                 "embedding": [],
#                 "position": chunk["position"]
#             })

#     return embeddings

# if __name__ == "__main__":
#     import yaml
#     import os
#     import llm_utils

#     # Load configuration
#     config=llm_utils.load_config()

#     logging.basicConfig(level=logging.INFO)

#     # Sample chunks for static test
#     test_chunks = [
#         {
#             "chunk_id": "test-1",
#             "text": "Terraform lets you define infrastructure as code and automate cloud provisioning.",
#             "position": 0
#         },
#         {
#             "chunk_id": "test-2",
#             "text": "HashiCorp Vault is a tool for securely accessing secrets.",
#             "position": 1
#         }
#     ]

#     # Run embedder
#     embedded = embed_chunks(test_chunks, config)

#     # Report results
#     for e in embedded:
#         dim = len(e["embedding"])
#         logging.info(f"Chunk {e['chunk_id']} embedded with {dim} dimensions")
#         print(f"{e['chunk_id']}: {str(e['embedding'])[:80]}...")  # preview

#     print("✅ Static embedding test completed.")
