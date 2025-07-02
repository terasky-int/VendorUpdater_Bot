"""
Enhanced main script for VendorUpdater_Bot that uses the new enhanced functions
"""

import os
import sys
import logging
import argparse
import time
import json
from datetime import datetime
from dotenv import load_dotenv

# Import email processing functions
from src import llm_utils, normalize, enrich, classify, chunker, embedder, indexer, manifest
from src.monitoring import check_health
from src.pipeline_tracker import PipelineTracker
from src.email_notifications import send_pipeline_summary_email

# Load environment variables
load_dotenv()

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="VendorUpdater_Bot Enhanced Pipeline")
    parser.add_argument("--deletelog", action="store_true", help="Delete log file before starting")
    parser.add_argument("--local", action="store_true", help="Use local email files instead of IMAP")
    parser.add_argument("--folder", type=str, default="data/emails", help="Folder with local email files")
    parser.add_argument("--cleanup", action="store_true", help="Clean up incorrect relationships")
    parser.add_argument("--confidence", type=str, default="medium", 
                        choices=["high", "medium", "low"], help="Minimum confidence level for relationships")
    parser.add_argument("--reset-db", action="store_true", help="Reset databases before starting")
    parser.add_argument("--emptydatafolders", action="store_true", help="Delete all files in data folders before running")
    parser.add_argument("--noevaluation", action="store_true", help="Skip evaluation step")
    return parser.parse_args()

def setup_logging(debug_mode=False):
    """Setup logging configuration"""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Configure file handler
    file_handler = logging.FileHandler(
        filename="logs/enhanced_pipeline.log",
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
    """Ensure value is a primitive type for storage"""
    if isinstance(value, list):
        return ", ".join(map(str, value))
    elif isinstance(value, (str, int, float, bool)) or value is None:
        return value
    else:
        return str(value)

def clean_data_folders():
    """Clean up data folders if needed"""
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

def reset_databases():
    """Reset ChromaDB and Neo4j databases"""
    logging.info("Resetting databases")
    
    # Reset ChromaDB
    try:
        from src.indexer import reset_chroma_db
        reset_chroma_db()
        logging.info("ChromaDB reset successfully")
    except Exception as e:
        logging.error(f"Failed to reset ChromaDB: {e}")
    
    # Neo4j reset functionality moved to TeraskyRag
    logging.info("Neo4j reset functionality moved to TeraskyRag repository")

def log_metrics(metrics_dict):
    """Log metrics to file"""
    try:
        os.makedirs("logs", exist_ok=True)
        metrics_file = "logs/metrics.jsonl"
        
        # Add timestamp
        metrics_dict["timestamp"] = datetime.now().isoformat()
        
        # Write to file
        with open(metrics_file, "a") as f:
            f.write(json.dumps(metrics_dict) + "\n")
            
        logging.debug(f"Logged metrics: {metrics_dict}")
    except Exception as e:
        logging.error(f"Failed to log metrics: {e}")

def run_pipeline():
    """Main pipeline function that processes emails sequentially"""
    start_time = time.time()
    emails_processed = 0
    
    # Initialize notification tracker
    tracker = PipelineTracker()
    tracker.start_run()
    
    try:
        config = load_config()

        setup_logging(config["debug"]["enabled"])
        logging.info("Starting VendorUpdater_Bot Enhanced Pipeline")
        logging.info(f"Current time: {datetime.now().isoformat()}")

        if args.emptydatafolders:
            clean_data_folders()
            
        # Reset databases if requested
        if args.reset_db:
            reset_databases()

        # Connect to ChromaDB collection once
        collection = llm_utils.get_chroma_collection()
        
        # Neo4j connection moved to TeraskyRag repository
        logging.info("Neo4j operations handled by TeraskyRag repository")
        graph = None

        # Harvest emails
        if args.local:
            if not args.folder:
                raise ValueError("--folder is required when using --local mode")
            from src.local_loader import load_local_emails
            emails = load_local_emails(args.folder)
            logging.info(f"Fetched {len(emails)} new emails from local files")
        else:
            from src.harvest import fetch_unread_emails
            emails = fetch_unread_emails(config)
            logging.info(f"Fetched {len(emails)} new emails from server")

        # Process each email sequentially
        for eid, email_obj in emails:
            try:
                # Import human debugging
                from src.human_debug import wait_for_user_input
                human_debug_enabled = config.get("debug", {}).get("human_in_the_middle", False)
                
                # Step 1: Save raw email
                from src.harvest import save_raw_email
                email_id, raw_path = save_raw_email(email_obj, config)
                logging.info(f"Processing email {email_id}")
                
                if human_debug_enabled:
                    if not wait_for_user_input("1_save_raw_email", {"email_obj": "Email object"}, {"email_id": email_id, "raw_path": raw_path}, email_id):
                        continue
                
                # Step 2: Normalize email
                clean_text = normalize.clean_email(raw_path, config, do_medium_clean=True)
                logging.info(f"Normalized email {email_id}")
                
                if human_debug_enabled:
                    if not wait_for_user_input("2_normalize_email", {"raw_path": raw_path}, {"clean_text": clean_text[:500] + "..." if len(clean_text) > 500 else clean_text}, email_id):
                        continue
                
                # Step 3: Enrich with metadata
                enriched_data = enrich.extract_metadata(clean_text, email_obj, config)
                logging.info(f"Enriched email {email_id} with metadata")
                
                if human_debug_enabled:
                    if not wait_for_user_input("3_extract_metadata", {"clean_text": clean_text[:200] + "..."}, enriched_data, email_id):
                        continue
                
                # Step 4: Classify content
                classified_data = classify.label_content(enriched_data, config)
                logging.info(f"Classified email {email_id} as {classified_data.get('type', 'unknown')}")
                
                # Track processed email for notifications
                tracker.add_processed_email(email_obj, classified_data)
                
                if human_debug_enabled:
                    if not wait_for_user_input("4_classify_content", enriched_data, classified_data, email_id):
                        continue
                
                # Step 5: Chunk text
                chunks = chunker.chunk_text(classified_data["text"], config)
                logging.info(f"Split email {email_id} into {len(chunks)} chunks")
                
                if human_debug_enabled:
                    chunk_summary = {"chunk_count": len(chunks), "chunks": [{"id": c["id"], "text": c["text"][:100] + "..."} for c in chunks[:3]]}
                    if not wait_for_user_input("5_chunk_text", {"text_length": len(classified_data["text"])}, chunk_summary, email_id):
                        continue
                
                # Step 6: Generate embeddings
                embeddings = embedder.embed_chunks(chunks, config)
                logging.info(f"Generated embeddings for email {email_id}")
                
                if human_debug_enabled:
                    embedding_summary = {"embedding_count": len(embeddings), "embedding_dimensions": len(embeddings[0]) if embeddings else 0}
                    if not wait_for_user_input("6_generate_embeddings", {"chunk_count": len(chunks)}, embedding_summary, email_id):
                        continue

                # Prepare metadata for indexing
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

                # Step 7: Index in local storage
                indexer.index(
                    chunks,
                    embeddings,
                    metadatas,
                    config
                )
                logging.info(f"Indexed email {email_id} in local storage")
                
                if human_debug_enabled:
                    index_summary = {"chunks_indexed": len(chunks), "metadata_sample": metadatas[0] if metadatas else {}}
                    if not wait_for_user_input("7_index_local", {"chunks": len(chunks), "embeddings": len(embeddings)}, index_summary, email_id):
                        continue

                # Record in manifest
                manifest.record_entry(email_id, chunks, classified_data, config)
                logging.info(f"Recorded email {email_id} in manifest")

                # Step 8: RAG evaluation moved to TeraskyRag repository
                logging.info(f"RAG evaluation for email {email_id} handled by TeraskyRag repository")

                # Merge embeddings into chunks
                for i, chunk in enumerate(chunks):
                    chunk["embedding"] = embeddings[i]

                    # Always ensure metadata is set
                    if "metadata" not in chunk:
                        chunk["metadata"] = {
                            "vendor": ensure_primitive(classified_data.get("vendor", "unknown")),
                            "product": ensure_primitive(classified_data.get("product", "unknown")),
                            "type": ensure_primitive(classified_data.get("type", "unknown")),
                            "date": ensure_primitive(classified_data.get("date", "1970-01-01"))
                        }

                # Filter valid chunks
                valid_chunks = [
                    c for c in chunks
                    if c.get("embedding") and isinstance(c.get("metadata"), dict)
                ]

                # Step 9: Index into ChromaDB
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
                
                # Step 10: Neo4j storage moved to TeraskyRag repository
                logging.info(f"Neo4j storage for email {email_id} handled by TeraskyRag repository")
                
                # Mark email as read if using IMAP
                if not args.local:
                    from src.harvest import mark_email_as_read
                    mark_email_as_read(eid, config)
                    
                doc_count = collection.count()
                logging.info(f"ChromaDB now contains {doc_count} total documents.")
                
                emails_processed += 1
                logging.info(f"Completed processing email {email_id} ({emails_processed}/{len(emails)})")
                
            except Exception as e:
                logging.error(f"Error processing email: {str(e)}")
                continue
        
        # Graph operations and unified search moved to TeraskyRag repository
        logging.info("Graph operations and search functionality handled by TeraskyRag repository")
        
        # Check system health (ingestion components only)
        health_status = check_health()
        logging.info(f"Ingestion system health: {health_status}")
        
        # Log successful completion
        end_time = time.time()
        processing_time = end_time - start_time
        log_metrics({
            "emails_processed": emails_processed,
            "processing_time": processing_time,
            "emails_per_second": emails_processed / processing_time if processing_time > 0 else 0
        })
        
        logging.info("Enhanced pipeline completed successfully")
        
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        tracker.set_error(str(e))
        log_metrics({
            "emails_processed": emails_processed,
            "error": str(e)
        })
        raise
    finally:
        # Send notification email regardless of success/failure
        try:
            summary = tracker.get_summary()
            send_pipeline_summary_email(config, summary)
        except Exception as e:
            logging.error(f"Failed to send notification: {e}")

def load_config(path="config/config.yaml"):
    """Load configuration from YAML file"""
    return llm_utils.load_config(path)

if __name__ == "__main__":
    global args
    args = parse_args()
    run_pipeline()