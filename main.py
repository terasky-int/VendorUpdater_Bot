import os
import logging
import yaml
from src import harvest, normalize, enrich, classify #, chunker, embedder, indexer, manifest, evaluate

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

# Main pipeline function
def run_pipeline():
    config = load_config()
    setup_logging(config["debug"]["enabled"])
    logging.info("Starting LLM data digestion pipeline")

    # Harvest
    emails = harvest.fetch_unread_emails(config)
    logging.info(f"Fetched {len(emails)} new emails")

    for eid, email_obj in emails:
        try:
            email_id, raw_path = harvest.save_raw_email(email_obj, config)
            clean_text = normalize.clean_email(raw_path, config)
            enriched_data = enrich.extract_metadata(clean_text, email_obj, config)
            classified_data = classify.label_content(enriched_data, config)
            # chunks = chunker.chunk_text(classified_data["text"], config)
            # embeddings = embedder.embed_chunks(chunks, config)
            # indexer.index(chunks, embeddings, classified_data, config)
            # manifest.record_entry(email_id, chunks, classified_data, config)

            # if config["debug"]["evaluation"]["enabled"]:
            #     evaluate.run_rag_test(email_id, chunks, config)

            logging.info(f"Successfully processed email ID {email_id}")
            harvest.mark_email_as_read(eid, config)


        except Exception as e:
            logging.error(f"Error processing email: {str(e)}")
            continue

if __name__ == "__main__":
    run_pipeline()