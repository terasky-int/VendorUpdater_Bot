import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import os
import csv
import logging
from src import llm_utils


def get_full_email_text(email_id: str) -> str:
    """Fetch the full cleaned email text from disk if available."""
    path = f"data/clean_text/{email_id}.txt"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""

def run_global_eval():
    config = llm_utils.load_config()
    collection = llm_utils.get_chroma_collection()

    query_list = config["debug"]["evaluation"].get("queries", [])
    top_k = config["debug"]["evaluation"].get("top_k", 3)
    show_conf = config["debug"]["evaluation"].get("show_confidence_score", True)

    os.makedirs("data/eval", exist_ok=True)
    output_path = "data/eval/GLOBAL_queries_eval.csv"

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Query", "Match #", "Score", "Document Snippet",
            "Vendor", "Product", "Type", "Date", "Email ID", "Chunk Index", "Full Email Text"
        ])

        for query in query_list:
            try:
                embedding = llm_utils.embed_text_titan(query)
                results = collection.query(query_embeddings=[embedding], n_results=top_k)

                for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
                    score = results["distances"][0][i] if show_conf else ""
                    email_id = meta.get("email_id", "")
                    chunk_index = meta.get("chunk_index", "")
                    full_email = get_full_email_text(email_id)

                    writer.writerow([
                        query,
                        i + 1,
                        score,
                        doc[:100],
                        meta.get("vendor", ""),
                        meta.get("product", ""),
                        meta.get("type", ""),
                        meta.get("date", ""),
                        email_id,
                        chunk_index,
                        full_email
                    ])

            except Exception as e:
                logging.error(f"Failed global query '{query}': {e}")

if __name__ == "__main__":
    run_global_eval()