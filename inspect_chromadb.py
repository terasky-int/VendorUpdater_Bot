from chromadb import PersistentClient
import json
from src import llm_utils

# Path to your ChromaDB directory (adjust if you use a custom path)
collection = llm_utils.get_chroma_collection()

# Total number of items
total = collection.count()
print(f"🔍 Collection '{collection.name}' contains {total} documents.\n")

# Batch query all documents (adjust `limit` if needed)
results = collection.get(include=["documents", "metadatas"])

# Visualize results
for idx, (doc, meta, doc_id) in enumerate(zip(results["documents"], results["metadatas"], results["ids"])):
    print(f"--- Document #{idx + 1} ---")
    print(f"🆔 ID: {doc_id}")
    print(f"📄 Text:\n{doc}\n")
    print(f"🧾 Metadata:\n{json.dumps(meta, indent=2)}\n")
