import os
import logging
import json

import yaml
from src import llm_utils, harvest, normalize, enrich, classify, chunker, embedder, indexer#, manifest, evaluate
import argparse
from dotenv import load_dotenv

parser = argparse.ArgumentParser(description="VendorUpdater Bot Pipeline")
parser.add_argument("--local", action="store_true", help="Run using local .eml files instead of a live server")
parser.add_argument("--folder", type=str, help="Path to folder containing .eml files (required with --local)")
parser.add_argument("--deletelog", action="store_true", help="delete log file before running the pipeline")
args = parser.parse_args()
load_dotenv()  # loads from .env in current working dir

# Load configuration
def load_config(path="config/config.yaml"):
    return llm_utils.load_config(path)

# Setup logging
def setup_logging(debug_mode):
    logging.basicConfig(
        filename="logs/pipeline.log",
        level=logging.DEBUG if debug_mode else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filemode="w" if args.deletelog else "a",
        encoding="utf-8"
    )
    if args.deletelog:
        logging.info("Log file deleted before running the pipeline")

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
    config = json.loads(json.dumps(config))  # convert to string
    config = yaml.safe_load(os.path.expandvars(json.dumps(config)))

            
    setup_logging(config["debug"]["enabled"])
    logging.info("Starting LLM data digestion pipeline")

    # Connect to ChromaDB collection once
    collection = llm_utils.get_chroma_collection()

    # Harvest emails
    if args.local:
        if not args.folder:
            raise ValueError("--folder is required when using --local mode")
        from src.local_loader import load_local_emails
        emails = load_local_emails(args.folder)
        logging.info(f"Fetched {len(emails)} new emails from local files")
    else:
        emails = harvest.fetch_unread_emails(config)
        logging.info(f"Fetched {len(emails)} new emails from server")

    for eid, email_obj in emails:
        try:
            email_id, raw_path = harvest.save_raw_email(email_obj, config)
            clean_text = normalize.clean_email(raw_path, config)
            enriched_data = enrich.extract_metadata(clean_text, email_obj, config)
            classified_data = classify.label_content(enriched_data, config)
            # logging.debug(f"Classified data: {classified_data}")
            chunks = chunker.chunk_text(classified_data["text"], config)

            embeddings = embedder.embed_chunks(chunks, config)

            ### WORK ON INDEXER - BUGGY !!!!!
            metadatas = [
                {
                    "vendor": ensure_primitive(classified_data.get("vendor", "unknown")),
                    "product": ensure_primitive(classified_data.get("product", "unknown")),
                    "type": ensure_primitive(classified_data.get("type", "unknown")),
                    "date": ensure_primitive(classified_data.get("date", "1970-01-01")),
                    "chunk_index": chunk["position"]
                }
                for chunk in chunks
            ]

            indexer.index(
                chunks,
                embeddings,
                metadatas,
                config   #TypeError('list indices must be integers or slices, not str')
            )

            # manifest.record_entry(email_id, chunks, classified_data, config)

            # if config["debug"]["evaluation"]["enabled"]:
            #     evaluate.run_rag_test(email_id, chunks, config)

            # Merge embeddings into chunks
            for i, chunk in enumerate(chunks):
                chunk["embedding"] = embeddings[i]

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
                
            if not args.local:
                harvest.mark_email_as_read(eid, config)
            doc_count = collection.count()
            logging.info(f"ChromaDB now contains {doc_count} total documents.")

        except Exception as e:
            logging.error(f"Error processing email: {str(e)}")
            continue

if __name__ == "__main__":
    run_pipeline()