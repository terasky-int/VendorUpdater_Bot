import logging
import boto3
import json
from typing import List

def embed_chunks(chunks: List[dict], config: dict) -> List[dict]:
    model_id = config["embedding"]["model"]
    client = boto3.client("bedrock-runtime")

    embeddings = []
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
            embeddings.append({
                "chunk_id": chunk["chunk_id"],
                "embedding": vector,
                "position": chunk["position"]
            })
            logging.debug(f"Embedded chunk {chunk['chunk_id']}")

        except Exception as e:
            logging.error(f"Embedding failed for chunk {chunk['chunk_id']}: {e}")
            embeddings.append({
                "chunk_id": chunk["chunk_id"],
                "embedding": [],
                "position": chunk["position"]
            })

    return embeddings
