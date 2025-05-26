import os
import csv
from src import llm_utils
from glob import glob

def get_full_email_text(email_id: str) -> str:
    clean_dir = "data/clean_text"
    txt_path = os.path.join(clean_dir, f"{email_id}.txt")
    if os.path.exists(txt_path):
        with open(txt_path, encoding="utf-8") as f:
            return f.read()
    return ""
    
def run_global_eval():
    config = llm_utils.load_config()
    collection = llm_utils.get_chroma_collection()

    query_list = config["debug"]["evaluation"].get("queries", [])
    top_k = config["debug"]["evaluation"].get("top_k", 3)
    show_conf = config["debug"]["evaluation"].get("show_confidence_score", True)

    cleaned_texts_dir = "data/clean_text"
    email_text_by_id = {
        os.path.splitext(f)[0]: open(os.path.join(cleaned_texts_dir, f), encoding="utf-8").read()
        for f in os.listdir(cleaned_texts_dir)
        if f.endswith(".txt")
    }

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
                    full_email = get_full_email_text(meta.get("email_id", ""))
                    writer.writerow([
                        query,
                        i + 1,
                        score,
                        doc[:100],
                        meta.get("email_id", ""),
                        meta.get("vendor", ""),
                        meta.get("product", ""),
                        meta.get("type", ""),
                        meta.get("date", ""),
                        full_email
                    ])
            except Exception as e:
                import logging
                logging.error(f"Failed global query '{query}': {e}")

if __name__ == "__main__":
    run_global_eval()


# import os
# import csv
# import yaml
# from src import llm_utils

# # Load configuration
# with open("config/config.yaml", "r", encoding="utf-8") as f:
#     config = yaml.safe_load(f)

# queries = config.get("debug", {}).get("evaluation", {}).get("queries", [])
# top_k = config.get("debug", {}).get("evaluation", {}).get("top_k", 3)
# show_conf = config.get("debug", {}).get("evaluation", {}).get("show_confidence_score", False)

# output_path = "data/eval/GLOBAL_queries_eval.csv"
# os.makedirs("data/eval", exist_ok=True)

# collection = llm_utils.get_chroma_collection()

# rows = []

# for query in queries:
#     try:
#         embedding = llm_utils.embed_text_titan(query)
#         results = collection.query(query_embeddings=[embedding], n_results=top_k)

#         for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
#             score = results["distances"][0][i] if show_conf else ""

#             row = {
#                 "query": query,
#                 "match_rank": i + 1,
#                 "score": score,
#                 "document_snippet": doc[:100]
#             }
#             for k, v in meta.items():
#                 row[f"meta_{k}"] = v

#             rows.append(row)

#     except Exception as e:
#         rows.append({
#             "query": query,
#             "match_rank": "",
#             "score": "",
#             "document_snippet": f"ERROR: {e}"
#         })

# # Gather all unique keys for dynamic header
# all_keys = sorted(set().union(*[row.keys() for row in rows]))

# with open(output_path, "w", encoding="utf-8", newline="") as f:
#     writer = csv.DictWriter(f, fieldnames=all_keys)
#     writer.writeheader()
#     writer.writerows(rows)

# print(f"✅ Global query evaluation saved to: {output_path}")
