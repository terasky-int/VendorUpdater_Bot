import os
import logging
import json
import time

import yaml
from src import llm_utils, harvest, normalize, enrich, classify, chunker, embedder, indexer, manifest, evaluate
from src.monitoring import log_metrics, check_health
from graph_db_enhanced  import *
import argparse
from dotenv import load_dotenv

parser = argparse.ArgumentParser(description="VendorUpdater Bot Pipeline")
parser.add_argument("--local", action="store_true", help="Run using local .eml files instead of a live server")
parser.add_argument("--folder", type=str, help="Path to folder containing .eml files (required with --local)")
parser.add_argument("--deletelog", action="store_true", help="delete log file before running the pipeline")
parser.add_argument("--emptydatafolders", action="store_true", help="delete all files in data folders before running the pipeline")
parser.add_argument("--noevaluation", action="store_true", help="skip evaluation step")
args = parser.parse_args()
load_dotenv()  # loads from .env in current working dir

# Load configuration
def load_config(path="config/config.yaml"):
    return llm_utils.load_config(path)

# Setup logging
def setup_logging(debug_mode):
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Configure file handler
    file_handler = logging.FileHandler(
        filename="logs/pipeline.log",
        mode="w" if args.deletelog else "a",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    
    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    if args.deletelog:
        logging.info("Log file deleted before running the pipeline")

def ensure_primitive(value):
    if isinstance(value, list):
        return ", ".join(map(str, value))
    elif isinstance(value, (str, int, float, bool)) or value is None:
        return value
    else:
        return str(value)

def clean_data_folders():
    """Clean up data folders if needed."""
    try:
        if not os.path.exists("data/clean_text"):
            os.makedirs("data/clean_text")
        else:
            for filename in os.listdir("data/clean_text"):
                file_path = os.path.join("data/clean_text", filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logging.info(f"Removed file: {file_path}")

        if not os.path.exists("data/raw_emails"):
            os.makedirs("data/raw_emails")
        else:
            for filename in os.listdir("data/raw_emails"):
                file_path = os.path.join("data/raw_emails", filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logging.info(f"Removed file: {file_path}")

        if not os.path.exists("data/eval"):
            os.makedirs("data/eval")
        else:
            for filename in os.listdir("data/eval"):
                file_path = os.path.join("data/eval", filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logging.info(f"Removed file: {file_path}")
                    
    except Exception as e:
        logging.error(f"Error cleaning data folders: {str(e)}")
        raise

# Main pipeline function
def run_pipeline():
    start_time = time.time()
    emails_processed = 0
    
    try:
        config = load_config()

        setup_logging(config["debug"]["enabled"])
        logging.info("Starting LLM data digestion pipeline")

        if args.emptydatafolders:
            clean_data_folders()

        # Connect to ChromaDB collection once
        collection = llm_utils.get_chroma_collection()
        
        # Connect to Neo4j and create schema
        graph = connect_to_graph()
        if graph:
            create_schema(graph)
            logging.info("Connected to Neo4j and created schema")
        else:
            logging.warning("Failed to connect to Neo4j, graph database features will be disabled")

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
                clean_text = normalize.clean_email(raw_path, config, do_medium_clean=True)
                enriched_data = enrich.extract_metadata(clean_text, email_obj, config)
                classified_data = classify.label_content(enriched_data, config)
                chunks = chunker.chunk_text(classified_data["text"], config)
                embeddings = embedder.embed_chunks(chunks, config)

                metadatas = [
                    {
                        "vendor": ensure_primitive(classified_data.get("vendor", "unknown")),
                        "product": ensure_primitive(classified_data.get("product", "unknown")),
                        "type": ensure_primitive(classified_data.get("type", "unknown")),
                        "date": ensure_primitive(classified_data.get("date", "1970-01-01")),
                        "chunk_index": chunk["position"],
                        "email_id": email_id 
                    }
                    for chunk in chunks
                ]

                indexer.index(
                    chunks,
                    embeddings,
                    metadatas,
                    config
                )

                manifest.record_entry(email_id, chunks, classified_data, config)

                # Skip evaluation if requested or if debug evaluation is disabled
                if not args.noevaluation and config["debug"]["evaluation"]["enabled"]:
                    try:
                        evaluate.run_rag_test(email_id, chunks, config)
                    except Exception as eval_error:
                        logging.error(f"Evaluation failed for email {email_id}: {str(eval_error)}")

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
                
                # Store in Neo4j
                if graph:
                    if add_email_to_graph_enhanced(graph, email_id, classified_data, clean_text):
                        logging.info(f"✅ Added email {email_id} to Neo4j graph database")
                    else:
                        logging.warning(f"⚠️ Failed to add email {email_id} to Neo4j")
                
                if not args.local:
                    harvest.mark_email_as_read(eid, config)
                    
                doc_count = collection.count()
                logging.info(f"ChromaDB now contains {doc_count} total documents.")
                
                emails_processed += 1

            except Exception as e:
                logging.error(f"Error processing email: {str(e)}")
                continue
                
        # Log successful completion
        log_metrics("pipeline_run", start_time, emails_processed=emails_processed)
        
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        log_metrics("pipeline_run", start_time, emails_processed=emails_processed, error=e)
        raise

if __name__ == "__main__":
    run_pipeline()