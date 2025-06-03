import os
import uuid
import json
import logging
from src import llm_utils, embedder

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Sample test data
test_documents = [
    {
        "text": "Hashicorp Vault 1.12.3 Security Update: Critical vulnerability CVE-2023-1234 has been patched. Update immediately to protect your secrets management infrastructure.",
        "metadata": {
            "vendor": "hashicorp",
            "product": "vault",
            "type": "security",
            "date": "2023-06-15"
        }
    },
    {
        "text": "Join our upcoming webinar on Cloud Security Best Practices featuring experts from AWS and Azure. Learn how to protect your cloud infrastructure from emerging threats.",
        "metadata": {
            "vendor": "aws",
            "product": "ec2",
            "type": "webinar",
            "date": "2023-07-20"
        }
    },
    {
        "text": "Terraform Cloud new feature announcement: Drift detection now available for all workspaces. Automatically detect and remediate configuration drift in your infrastructure.",
        "metadata": {
            "vendor": "hashicorp",
            "product": "terraform cloud",
            "type": "product update",
            "date": "2023-08-05"
        }
    },
    {
        "text": "Palo Alto Cortex XDR security advisory: Update to version 8.6.2 to address multiple vulnerabilities that could allow remote code execution.",
        "metadata": {
            "vendor": "palo alto",
            "product": "cortex xdr",
            "type": "security",
            "date": "2023-09-10"
        }
    },
    {
        "text": "AWS Summit 2023: Join us for a day of learning about the latest AWS services and best practices. Register now for our cloud security workshop.",
        "metadata": {
            "vendor": "aws",
            "product": "aws",
            "type": "event",
            "date": "2023-10-15"
        }
    }
]

def load_test_data():
    """Load test data into ChromaDB"""
    collection = llm_utils.get_chroma_collection()
    
    # Check if collection already has documents
    count = collection.count()
    logging.info(f"Current document count: {count}")
    
    # Prepare data for insertion
    texts = [doc["text"] for doc in test_documents]
    metadatas = [doc["metadata"] for doc in test_documents]
    ids = [f"test-{uuid.uuid4()}" for _ in range(len(test_documents))]
    
    # Generate embeddings
    config = llm_utils.load_config()
    embeddings = embedder.embed_chunks([{"text": text} for text in texts], config)
    
    # Add to collection
    collection.add(
        documents=texts,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings
    )
    
    new_count = collection.count()
    logging.info(f"Added {new_count - count} test documents. New count: {new_count}")
    
    return ids

if __name__ == "__main__":
    load_test_data()