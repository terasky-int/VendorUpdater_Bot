"""
Debug API for testing RAG functionality
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import logging
from src import llm_utils

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(title="Debug API")

@app.get("/raw_search")
async def raw_search(query: str, limit: int = 10):
    """
    Perform a raw search without any filtering to debug results
    """
    try:
        collection = llm_utils.get_chroma_collection()
        
        # Generate proper embeddings using the Titan model
        query_embedding = llm_utils.embed_text_titan(query)
        logging.info(f"Generated embedding with dimension: {len(query_embedding)}")
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = {
            "documents": results["documents"][0] if results["documents"] and len(results["documents"]) > 0 else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] and len(results["metadatas"]) > 0 else [],
            "distances": results["distances"][0] if results["distances"] and len(results["distances"]) > 0 else [],
            "ids": results["ids"][0] if results["ids"] and len(results["ids"]) > 0 else []
        }
        
        return {
            "query": query,
            "embedding_dimension": len(query_embedding),
            "total_results": len(formatted_results["documents"]),
            "results": [
                {
                    "document_preview": doc[:200] + "..." if len(doc) > 200 else doc,
                    "metadata": meta,
                    "distance": dist
                }
                for doc, meta, dist in zip(
                    formatted_results["documents"], 
                    formatted_results["metadatas"], 
                    formatted_results["distances"]
                )
            ]
        }
    except Exception as e:
        logging.error(f"Raw search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collection_info")
async def collection_info():
    """
    Get detailed information about the collection
    """
    try:
        collection = llm_utils.get_chroma_collection()
        count = collection.count()
        
        # Get sample data
        if count > 0:
            sample = collection.get(limit=min(5, count))
            
            # Extract unique metadata keys
            all_keys = set()
            for meta in sample["metadatas"]:
                all_keys.update(meta.keys())
            
            # Count documents by vendor
            vendors = {}
            all_data = collection.get()
            for meta in all_data["metadatas"]:
                vendor = meta.get("vendor", "unknown")
                vendors[vendor] = vendors.get(vendor, 0) + 1
            
            return {
                "collection_name": collection.name,
                "document_count": count,
                "metadata_keys": list(all_keys),
                "vendors": vendors,
                "sample_documents": [
                    {
                        "document_preview": doc[:100] + "..." if len(doc) > 100 else doc,
                        "metadata": meta
                    }
                    for doc, meta in zip(sample["documents"], sample["metadatas"])
                ]
            }
        else:
            return {"collection_name": collection.name, "document_count": 0}
    except Exception as e:
        logging.error(f"Error getting collection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test_embedding")
async def test_embedding(text: str = "Test embedding generation"):
    """
    Test embedding generation to check dimensions
    """
    try:
        embedding = llm_utils.embed_text_titan(text)
        return {
            "text": text,
            "embedding_dimension": len(embedding),
            "embedding_sample": embedding[:5]  # Show just the first 5 values
        }
    except Exception as e:
        logging.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)