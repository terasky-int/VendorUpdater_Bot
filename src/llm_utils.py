# src/llm_utils.py
import json
import yaml
import boto3
import logging
from chromadb import PersistentClient

def load_config(path="config/config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def get_chroma_collection(config):
    client = PersistentClient(path=config["vector_store"]["persist_directory"])
    return client.get_or_create_collection(name=config["vector_store"]["collection_name"])

def embed_text_titan(text: str, config: dict) -> list:
    try:
        bedrock_client = boto3.client("bedrock-runtime", region_name=config["bedrock"]["region"])
        response = bedrock_client.invoke_model(
            modelId=config["embedding"]["model"],
            body=json.dumps({"inputText": text}),
            contentType="application/json",
            accept="application/json"
        )
        body = json.loads(response["body"].read().decode("utf-8"))
        return body["embedding"]
    except Exception as e:
        logging.error(f"Embedding failed for text: {text[:100]} — {str(e)}")
        raise
