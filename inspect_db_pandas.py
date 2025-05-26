import pandas as pd
from src import llm_utils
import argparse

parser = argparse.ArgumentParser(description="ChromaDB Inspection Script")
parser.add_argument("--csvout", action="store_true", help="export results to CSV")
parser.add_argument("--stdout", action="store_true", help="export results to STDOUT")
parser.add_argument("--csvpath", type=str, help="Path to the output CSV file")
args = parser.parse_args()

if __name__ == "__main__":

    collection = llm_utils.get_chroma_collection()
    results = collection.get(include=["documents", "metadatas"])

    rows = []

    for doc, meta, doc_id in zip(results["documents"], results["metadatas"], results["ids"]):
        flat_meta = {k: str(v) for k, v in meta.items()}
        rows.append({"id": doc_id, "text": doc[:300], **flat_meta})  # truncate long text

    df = pd.DataFrame(rows)
    if args.csvout:
        if not args.csvpath:
            raise ValueError("--csvpath is required when using --csvout mode")
        try:
            df.to_csv(args.csvpath, index=False)
        except Exception as e:
            print(f"Error writing to CSV: {e}")
            exit(1)
            
    if args.stdout:
        print(df.head())
        
        
