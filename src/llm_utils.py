import json
import yaml
import boto3
import logging
from typing import List, Optional
from chromadb import PersistentClient
from chromadb.api.models.Collection import Collection
import os

CONFIG_PATH = "config/config.yaml"

# ----------------------------------------------------------------------
# ✅ Configuration Loader
# ----------------------------------------------------------------------
def load_config(path: str = CONFIG_PATH) -> dict:
    with open(path, "r") as f:
        config = json.loads(os.path.expandvars(json.dumps(yaml.safe_load(f))))  # convert to string
        # config = yaml.safe_load((config)))
        return config

# ----------------------------------------------------------------------
# ✅ ChromaDB Collection Accessor
# ----------------------------------------------------------------------
def get_chroma_collection() -> Collection:
    config = load_config()
    chroma_path = config["vector_store"].get("persist_directory", "data/chroma")
    collection_name = config["vector_store"].get("collection_name", "vendor_emails")
    client = PersistentClient(path=chroma_path)
    return client.get_or_create_collection(name=collection_name)

# ----------------------------------------------------------------------
# ✅ Titan Embedding Function
# ----------------------------------------------------------------------
def embed_text_titan(text: str) -> List[float]:
    config = load_config()

    region = config.get("embedding", {}).get("region", "eu-west-1")
    model_id = config.get("embedding", {}).get("model", "amazon.titan-embed-text-v2:0")

    try:
        bedrock_client = boto3.client("bedrock-runtime", region_name=region)
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps({"inputText": text}),
            contentType="application/json",
            accept="application/json"
        )
        response_body = json.loads(response["body"].read())
        return response_body["embedding"]

    except Exception as e:
        logging.error(f"❌ Embedding failed for text: {text[:100]}... — {str(e)}")
        raise


def generate_claude_answer(context_docs: list, question: str, config: dict) -> str:
    """
    Generate a natural language answer using Claude (via Bedrock).
    """
    try:
        model_id = config["rag"]["answer_model"]
        client = boto3.client("bedrock-runtime")

        context = "\n\n".join(context_docs)
        prompt = (
            "You are a helpful assistant analyzing vendor emails.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}]
        }

        response = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )

        result = json.loads(response["body"].read())
        return result.get("content", [])[0].get("text", "").strip()

    except Exception as e:
        logging.error(f"❌ Failed to generate answer with Claude: {e}")
        return "❌ Claude generation failed"
    