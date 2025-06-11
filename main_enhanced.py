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

# Import enhanced functions from graph_db
from graph_db import (
    import_all_emails_enhanced,
    cleanup_incorrect_relationships,
    get_graph_summary,
    get_vendor_products_by_confidence,
    connect_to_graph,
    create_schema,
    add_email_to_graph_enhanced,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW
)

# Import unified search functions
from src.unified_search import (
    unified_search,
    process_search_query,
    graph_enhanced_ranking
)

# Import email processing functions
from src import llm_utils, normalize, enrich, classify, chunker, embedder, indexer, manifest, evaluate
from src.monitoring import check_health

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
    
    # Reset Neo4j
    try:
        graph = connect_to_graph()
        if graph:
            graph.run("MATCH (n) DETACH DELETE n")
            logging.info("Neo4j database reset successfully")
    except Exception as e:
        logging.error(f"Failed to reset Neo4j database: {e}")

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
            from src.harvest import fetch_unread_emails
            emails = fetch_unread_emails(config)
            logging.info(f"Fetched {len(emails)} new emails from server")

        # Process each email sequentially
        for eid, email_obj in emails:
            try:
                # Step 1: Save raw email
                from src.harvest import save_raw_email
                email_id, raw_path = save_raw_email(email_obj, config)
                logging.info(f"Processing email {email_id}")
                
                # Step 2: Normalize email
                clean_text = normalize.clean_email(raw_path, config, do_medium_clean=True)
                logging.info(f"Normalized email {email_id}")
                
                # Step 3: Enrich with metadata
                enriched_data = enrich.extract_metadata(clean_text, email_obj, config)
                logging.info(f"Enriched email {email_id} with metadata")
                
                # Step 4: Classify content
                classified_data = classify.label_content(enriched_data, config)
                logging.info(f"Classified email {email_id} as {classified_data.get('type', 'unknown')}")
                
                # Step 5: Chunk text
                chunks = chunker.chunk_text(classified_data["text"], config)
                logging.info(f"Split email {email_id} into {len(chunks)} chunks")
                
                # Step 6: Generate embeddings
                embeddings = embedder.embed_chunks(chunks, config)
                logging.info(f"Generated embeddings for email {email_id}")

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

                # Record in manifest
                manifest.record_entry(email_id, chunks, classified_data, config)
                logging.info(f"Recorded email {email_id} in manifest")

                # Step 8: Run evaluation if enabled
                if not args.noevaluation and config["debug"]["evaluation"]["enabled"]:
                    try:
                        evaluate.run_rag_test(email_id, chunks, config)
                        logging.info(f"Evaluated RAG performance for email {email_id}")
                    except Exception as eval_error:
                        logging.error(f"Evaluation failed for email {email_id}: {str(eval_error)}")

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
                
                # Step 10: Store in Neo4j with enhanced validation
                if graph:
                    if add_email_to_graph_enhanced(graph, email_id, classified_data, clean_text):
                        logging.info(f"✅ Added email {email_id} to Neo4j graph database with enhanced validation")
                    else:
                        logging.warning(f"⚠️ Failed to add email {email_id} to Neo4j")
                
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
        
        # Clean up incorrect relationships if requested
        if args.cleanup:
            logging.info("Cleaning up incorrect relationships")
            cleanup_incorrect_relationships()
        
        # Get graph summary
        logging.info("Getting graph database summary")
        summary = get_graph_summary()
        if summary:
            logging.info("Graph Database Summary:")
            if "node_counts" in summary and summary["node_counts"]:
                logging.info("Node counts:")
                for item in summary["node_counts"]:
                    logging.info(f"- {item['label']}: {item['count']}")
            
            if "relationship_counts" in summary and summary["relationship_counts"]:
                logging.info("Relationship counts:")
                for item in summary["relationship_counts"]:
                    logging.info(f"- {item['relationship_type']}: {item['count']}")
        
        # Get vendor products with confidence level
        vendor = "hashicorp"  # Example vendor
        confidence_map = {
            "high": CONFIDENCE_HIGH,
            "medium": CONFIDENCE_MEDIUM,
            "low": CONFIDENCE_LOW
        }
        confidence = confidence_map.get(args.confidence, CONFIDENCE_MEDIUM)
        
        logging.info(f"Getting products for vendor '{vendor}' with confidence level '{args.confidence}'")
        products = get_vendor_products_by_confidence(vendor, confidence)
        
        if products:
            logging.info(f"Found {len(products)} products for vendor '{vendor}':")
            for product in products:
                logging.info(f"- {product['product']} (confidence: {product['confidence']})")
        else:
            logging.info(f"No products found for vendor '{vendor}'")
        
        # Test unified search
        query = "Show me recent security updates from hashicorp about vault"
        logging.info(f"Testing unified search with query: '{query}'")
        
        processed = process_search_query(query)
        logging.info(f"Processed query: {processed}")
        
        results = unified_search(
            processed["query_text"],
            processed["filters"],
            processed["graph_filters"],
            5
        )
        
        if results["documents"]:
            logging.info(f"Found {len(results['documents'])} results")
            logging.info("Top result:")
            logging.info(f"- Document: {results['documents'][0][:100]}...")
            logging.info(f"- Metadata: {results['metadatas'][0]}")
        else:
            logging.info("No results found")
        
        # Check system health
        health_status = check_health()
        logging.info(f"System health: {health_status}")
        
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
        log_metrics({
            "emails_processed": emails_processed,
            "error": str(e)
        })
        raise

def load_config(path="config/config.yaml"):
    """Load configuration from YAML file"""
    return llm_utils.load_config(path)

if __name__ == "__main__":
    global args
    args = parse_args()
    run_pipeline()