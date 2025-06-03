from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import logging
import json
from src.hybrid_search import hybrid_search
from src import llm_utils

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(title="Vendor Email RAG API")

class QueryRequest(BaseModel):
    query: str
    metadata_filters: Optional[Dict[str, str]] = None
    top_k: int = 5

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    try:
        # Load config
        config = llm_utils.load_config()
        
        # Log request
        logging.info(f"Query request: {request.query}")
        if request.metadata_filters:
            logging.info(f"Filters: {request.metadata_filters}")
        
        # Perform hybrid search
        search_results = hybrid_search(
            request.query, 
            request.metadata_filters, 
            request.top_k
        )
        
        # Check if we got any results
        if not search_results["documents"]:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "sources": []
            }
        
        # Generate answer using retrieved documents
        documents = search_results["documents"]
        
        # For testing without calling Bedrock
        if "test" in request.query.lower():
            answer = "This is a test response without calling the LLM API."
        else:
            try:
                answer = llm_utils.generate_claude_answer(documents, request.query, config)
            except Exception as e:
                logging.error(f"Error generating answer: {str(e)}")
                answer = f"I found some relevant information but couldn't generate a complete answer. Here's a summary of what I found: {documents[0][:200]}..."
        
        # Format sources
        sources = []
        for i, (doc, meta) in enumerate(zip(search_results["documents"], search_results["metadatas"])):
            sources.append({
                "text": doc[:200] + "..." if len(doc) > 200 else doc,
                "metadata": meta
            })
        
        return {"answer": answer, "sources": sources}
    
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    try:
        # Check if ChromaDB is accessible
        collection = llm_utils.get_chroma_collection()
        count = collection.count()
        return {"status": "healthy", "document_count": count}
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metadata")
async def get_metadata():
    """Get unique metadata values from the collection"""
    try:
        collection = llm_utils.get_chroma_collection()
        all_data = collection.get()
        
        vendors = list(set(m.get("vendor", "unknown") for m in all_data["metadatas"]))
        products = list(set(m.get("product", "unknown") for m in all_data["metadatas"]))
        types = list(set(m.get("type", "unknown") for m in all_data["metadatas"]))
        
        return {
            "vendors": vendors,
            "products": products,
            "types": types
        }
    except Exception as e:
        logging.error(f"Error getting metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)