# src/indexer.py
import logging
from src.llm_utils import load_config, get_chroma_collection

def index_chunks(chunks, config):
    try:
        config = load_config()
        collection = get_chroma_collection(config)

        valid_chunks = [
            c for c in chunks
            if c.get("embedding") and isinstance(c.get("metadata"), dict)
        ]

        if not valid_chunks:
            logging.warning("⚠️ No valid chunks to index.")
            return

        collection.add(
            documents=[c["text"] for c in valid_chunks],
            metadatas=[c["metadata"] for c in valid_chunks],
            ids=[c["chunk_id"] for c in valid_chunks],
            embeddings=[c["embedding"] for c in valid_chunks]
        )
        logging.info(f"✅ Indexed {len(valid_chunks)} chunks into ChromaDB.")

    except Exception as e:
        logging.error(f"❌ Failed to index chunks: {str(e)}")
