import logging
import boto3
import json
from typing import List


def embed_text(text: str) -> List[float]:
    """Generate embedding for a single text string"""
    try:
        client = boto3.client("bedrock-runtime", region_name="eu-west-1")
        response = client.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps({"inputText": text}),
            contentType="application/json",
            accept="application/json"
        )
        response_body = json.loads(response["body"].read())
        return response_body["embedding"]
    except Exception as e:
        logging.error(f"❌ Embedding failed for text: {text[:100]}... — {str(e)}")
        raise


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

