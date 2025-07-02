import os
import csv
import logging
from src import llm_utils

def run_rag_test(email_id, chunks, config):
    if not config.get("debug", {}).get("evaluation", {}).get("enabled", False):
        logging.info("Evaluation disabled via config")
        return

    top_k = config["debug"]["evaluation"].get("top_k", 3)
    show_conf = config["debug"]["evaluation"].get("show_confidence_score", False)
    output_dir = "data/eval"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{email_id}_eval.csv")

    collection = llm_utils.get_chroma_collection()

    with open(output_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Query", "Match #", "Score", "Document Snippet", "Metadata"])

        for chunk in chunks:
            query = chunk["text"][:200]  # Use the first 200 characters of the chunk as a proxy query

            try:
                # Embed the query using the configured model
                provider = config.get("embedding", {}).get("provider", "amazon")
                if provider == "amazon":
                    embedding = llm_utils.embed_text_titan(query)
                else:
                    raise ValueError(f"Unsupported embedder provider for evaluation: {provider}")

                result = collection.query(
                    query_embeddings=[embedding],
                    n_results=top_k
                )

                for i, (doc, meta) in enumerate(zip(result["documents"][0], result["metadatas"][0])):
                    score = result["distances"][0][i] if show_conf else ""
                    writer.writerow([query, i + 1, score, doc[:100], meta])

            except Exception as e:
                logging.error(f"Evaluation query failed: {e}")
