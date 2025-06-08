import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import os
import csv
import logging
from datetime import datetime
from src import llm_utils

def run_rag_answers():
    config = llm_utils.load_config()
    collection = llm_utils.get_chroma_collection()

    query_list = config["debug"]["evaluation"].get("queries", [])
    top_k = config["debug"]["evaluation"].get("top_k", 3)
    model = config["embedding"]["model"]

    output_dir = "data/eval"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, "GLOBAL_queries_rag_answers.csv")

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Query", "RAG Answer", "Top Documents Context",
            "Vendor", "Product", "Type", "Date", "Email ID"
        ])

        for query in query_list:
            try:
                # Embed the query
                embedding = llm_utils.embed_text_titan(query)

                # Retrieve top-k documents from Chroma
                results = collection.query(query_embeddings=[embedding], n_results=top_k)

                contexts = results["documents"][0]
                metadatas = results["metadatas"][0]
                print(query)
                
                # Compose the prompt
                context_text = "\n\n---\n\n".join(contexts)
                print(context_text)
                prompt = f"""You are an assistant helping a user answer questions based on vendor emails.
Use the following documents to answer the query as accurately and informatively as possible.

Query: {query}

Documents:
{context_text}

Answer:"""
                
                docs = results["documents"][0]
                # Call Claude for the answer
                answer = llm_utils.generate_claude_answer(docs, query, config=config)
                print(answer)
                print("\n\n")
                for i, metadata in enumerate(metadatas):
                    writer.writerow([
                        query,
                        answer,
                        contexts[i][:300],  # Snippet of doc context
                        metadata.get("vendor", ""),
                        metadata.get("product", ""),
                        metadata.get("type", ""),
                        metadata.get("date", ""),
                        metadata.get("email_id", "")
                    ])
                logging.info(f"✅ Answered query: {query}")

            except Exception as e:
                logging.error(f"❌ Failed to answer query '{query}': {e}")

    logging.info(f"✅ All RAG answers written to: {output_path}")

if __name__ == "__main__":
    run_rag_answers()