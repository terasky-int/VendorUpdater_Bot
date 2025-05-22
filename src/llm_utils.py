import json
import yaml
import boto3
import logging
from typing import List, Optional
from chromadb import PersistentClient
from chromadb.api.models.Collection import Collection

CONFIG_PATH = "config/config.yaml"

# ----------------------------------------------------------------------
# ✅ Configuration Loader
# ----------------------------------------------------------------------
def load_config(path: str = CONFIG_PATH) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)

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
