# What It Does:
# Uses langchain.text_splitter.RecursiveCharacterTextSplitter to split the cleaned email into chunks

# Respects:

# chunk_size_tokens: typically 512

# chunk_overlap: typically 20

# Assigns each chunk a chunk_id and position for traceability

# Optionally saves the output to data/chunks/ for debugging if enabled in config.yaml

import os
import logging
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter


def chunk_text(text: str, config: dict) -> List[dict]:
    chunk_size = config["data_processing"].get("chunk_size_tokens", 512)
    chunk_overlap = config["data_processing"].get("chunk_overlap", 20)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )

    raw_chunks = splitter.split_text(text)
    logging.info(f"Split text into {len(raw_chunks)} chunks")

    chunks = []
    for i, chunk in enumerate(raw_chunks):
        chunks.append({
            "chunk_id": f"chunk-{i}",
            "text": chunk,
            "position": i
        })

    # Save chunks for debugging
    if config["debug"].get("save_all_artifacts", False):
        os.makedirs("data/chunks", exist_ok=True)
        out_path = os.path.join("data/chunks", f"chunks_{len(chunks)}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            import json
            json.dump(chunks, f, indent=2, ensure_ascii=False)

    return chunks
