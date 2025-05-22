import os
import logging
import yaml
import json
from chromadb import PersistentClient
from src import harvest, normalize, enrich, classify, chunker, embedder #, indexer, manifest, evaluate

# Load configuration
def load_config(path="config/config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

# Setup logging
def setup_logging(debug_mode):
    logging.basicConfig(
        filename="logs/pipeline.log",
        level=logging.DEBUG if debug_mode else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

def ensure_primitive(value):
    if isinstance(value, list):
        return ", ".join(map(str, value))
    elif isinstance(value, (str, int, float, bool)) or value is None:
        return value
    else:
        return str(value)
    
# Main pipeline function
def run_pipeline():
    config = load_config()
    setup_logging(config["debug"]["enabled"])
    logging.info("Starting LLM data digestion pipeline")

    # Connect to ChromaDB collection once
    chroma_path = config["vector_store"]["persist_directory"]
    collection_name = config["vector_store"]["collection_name"]
    client = PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(name=collection_name)

    # Harvest
    emails = harvest.fetch_unread_emails(config)
    logging.info(f"Fetched {len(emails)} new emails")

    for eid, email_obj in emails:
        try:
            email_id, raw_path = harvest.save_raw_email(email_obj, config)
            clean_text = normalize.clean_email(raw_path, config)
            enriched_data = enrich.extract_metadata(clean_text, email_obj, config)
            classified_data = classify.label_content(enriched_data, config)
            logging.debug(f"Classified types: {classified_data.get('type')}")
            chunks = chunker.chunk_text(classified_data["text"], config)
            embeddings = embedder.embed_chunks(chunks, config)
            # print(f"Embedded {len(embeddings)} chunks.")
            # print(embeddings[0])  # Show a sample vector
            # indexer.index(chunks, embeddings, classified_data, config)
            # manifest.record_entry(email_id, chunks, classified_data, config)

            # if config["debug"]["evaluation"]["enabled"]:
            #     evaluate.run_rag_test(email_id, chunks, config)

            # Merge embeddings into chunks
            for chunk in chunks:
                match = next((e for e in embeddings if e["chunk_id"] == chunk["chunk_id"]), None)
                if match and match["embedding"]:
                    chunk["embedding"] = match["embedding"]

                # ✅ Always ensure metadata is set
                if "metadata" not in chunk:
                    chunk["metadata"] = {
                        "vendor": ensure_primitive(classified_data.get("vendor", "unknown")),
                        "product": ensure_primitive(classified_data.get("product", "unknown")),
                        "type": ensure_primitive(classified_data.get("type", "unknown")),
                        "date": ensure_primitive(classified_data.get("date", "1970-01-01"))
                    }

            valid_chunks = [
                c for c in chunks
                if c.get("embedding") and isinstance(c.get("metadata"), dict)
            ]

            # Index into ChromaDB
            if valid_chunks:
                collection.add(
                    documents=[c["text"] for c in valid_chunks],
                    metadatas=[c["metadata"] for c in valid_chunks],
                    ids=[c["chunk_id"] for c in valid_chunks],
                    embeddings=[c["embedding"] for c in valid_chunks]
                )
                logging.info(f"✅ Embedded and stored {len(valid_chunks)} chunks for email ID {email_id}")
                for i, chunk in enumerate(valid_chunks):
                    try:
                        json.dumps(chunk["metadata"])
                    except Exception as e:
                        logging.error(f"Invalid metadata in chunk {i}: {chunk['metadata']}, error: {str(e)}")
            else:
                logging.warning(f"⚠️ No valid chunks for email ID {email_id}")
                

            harvest.mark_email_as_read(eid, config)
            doc_count = collection.count()
            logging.info(f"ChromaDB now contains {doc_count} total documents.")

        except Exception as e:
            logging.error(f"Error processing email: {str(e)}")
            continue

if __name__ == "__main__":
    run_pipeline()