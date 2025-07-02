from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import logging
import json
from datetime import datetime
from src import llm_utils

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(title="Vendor Email RAG API")

class QueryRequest(BaseModel):
    query: str
    metadata_filters: Optional[Dict[str, str]] = None
    top_k: int = 5
    include_expired: bool = False

class MultiValueQueryRequest(BaseModel):
    query: str
    metadata_filters: Optional[Dict[str, List[str]]] = None
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
        
        # Process filters - extract special filters that need post-processing
        where_clause = {}
        special_filters = {}
        
        if request.metadata_filters:
            for key, value in request.metadata_filters.items():
                # Convert to special filters for type and product
                if key in ["type", "product"]:
                    special_filters[key] = value
                else:
                    # Regular filters go directly to the where clause
                    where_clause[key] = value
        
        logging.info(f"Using where clause: {where_clause}")
        if special_filters:
            logging.info(f"Using special filters for post-processing: {special_filters}")
        
        # Perform metadata-only search
        collection = llm_utils.get_chroma_collection()
        logging.info(f"Collection has {collection.count()} documents")
        
        try:
            # First try metadata-only search
            results = collection.get(
                where=where_clause if where_clause else None,
                limit=request.top_k * 3  # Get more results for post-filtering
            )
            
            # Format initial results
            search_results = {
                "documents": results["documents"] if "documents" in results else [],
                "metadatas": results["metadatas"] if "metadatas" in results else [],
                "distances": [1.0] * len(results["documents"]) if "documents" in results else [],  # Placeholder distances
                "ids": results["ids"] if "ids" in results else []
            }
            
            # Apply post-filtering for special filters and expiration
            if (special_filters or not request.include_expired) and search_results["metadatas"]:
                filtered_docs = []
                filtered_metas = []
                filtered_distances = []
                filtered_ids = []
                current_date = datetime.now().date()
                
                for i, meta in enumerate(search_results["metadatas"]):
                    include_item = True
                    
                    # Check each special filter
                    for field, search_term in special_filters.items():
                        field_value = meta.get(field, "")
                        if search_term.lower() not in field_value.lower():
                            include_item = False
                            break
                    
                    # Check expiration if not including expired content
                    if include_item and not request.include_expired:
                        for date_field in ["event_date", "registration_deadline", "expiration_date"]:
                            date_value = meta.get(date_field)
                            if date_value:
                                try:
                                    event_date = datetime.fromisoformat(date_value).date()
                                    if event_date < current_date:
                                        include_item = False
                                        break
                                except Exception as e:
                                    logging.exception("Error parsing date", exc_info=True)  # Log the exception details
                    
                    if include_item:
                        filtered_docs.append(search_results["documents"][i])
                        filtered_metas.append(search_results["metadatas"][i])
                        filtered_distances.append(search_results["distances"][i])
                        filtered_ids.append(search_results["ids"][i])
                
                # Update results with filtered items
                search_results = {
                    "documents": filtered_docs[:request.top_k],
                    "metadatas": filtered_metas[:request.top_k],
                    "distances": filtered_distances[:request.top_k],
                    "ids": filtered_ids[:request.top_k]
                }
            
            logging.info(f"Search returned {len(search_results['documents'])} results")
        except Exception as e:
            logging.error(f"Search failed: {e}")
            search_results = {
                "documents": [],
                "metadatas": [],
                "distances": [],
                "ids": []
            }
        
        # Check if we got any results
        if not search_results["documents"]:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "sources": []
            }
        
        # Generate answer using retrieved documents
        documents = search_results["documents"]
        
        # For testing without calling Bedrock - only exact "test query" should trigger this
        if request.query.lower() == "test query":
            answer = "This is a test response without calling the LLM API."
            # Include debug info in test mode
            answer += f"\n\nDebug info:\nQuery: {request.query}\nFilters: {request.metadata_filters}\nResults: {len(documents)} documents found"
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
        
        # Get sample document to verify data structure
        sample = None
        if count > 0:
            try:
                sample_data = collection.get(limit=1)
                if sample_data and sample_data["metadatas"]:
                    sample = {
                        "metadata_keys": list(sample_data["metadatas"][0].keys()),
                        "document_preview": sample_data["documents"][0][:100] if sample_data["documents"] else "No document content"
                    }
            except Exception as e:
                sample = {"error": str(e)}
        
        return {
            "status": "healthy", 
            "document_count": count,
            "sample_document": sample
        }
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
        
        # Add detailed metadata for debugging
        sample_metadata = all_data["metadatas"][:5] if all_data["metadatas"] else []
        
        return {
            "vendors": vendors,
            "products": products,
            "types": types,
            "sample_metadata": sample_metadata,
            "total_documents": collection.count()
        }
    except Exception as e:
        logging.error(f"Error getting metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)