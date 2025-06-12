"""
Unified API for VendorUpdater_Bot

This module consolidates all API endpoints (RAG, Graph, Debug) into a single API with different routes.
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import logging
import json

# Import from src modules
from src import llm_utils
from src.optimized_search import (
    process_search_query,
    unified_search,
    graph_enhanced_ranking,
    format_search_results,
    get_vendor_products_enhanced
)

# Import from graph database
from graph_db_consolidated import (
    get_vendor_products, 
    get_related_vendors, 
    get_email_timeline,
    run_graph_query,
    mock_graph_data,
    count_vendor_emails,
    count_recent_emails,
    find_security_emails,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Create FastAPI app
app = FastAPI(title="VendorUpdater Bot API", description="Unified API for vendor email processing")

# Define request/response models
class QueryRequest(BaseModel):
    query: str
    metadata_filters: Optional[Dict[str, str]] = None
    top_k: int = 5

class MultiValueQueryRequest(BaseModel):
    query: str
    metadata_filters: Optional[Dict[str, List[str]]] = None
    top_k: int = 5

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

class GraphQueryRequest(BaseModel):
    query: str
    params: Optional[Dict[str, Any]] = None

# RAG API Routes
@app.post("/rag/query", response_model=QueryResponse, tags=["RAG"])
async def rag_query(request: QueryRequest):
    """
    Process a RAG query and return an answer with sources
    """
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
        
        # Perform metadata-only search
        collection = llm_utils.get_chroma_collection()
        
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
                "distances": [1.0] * len(results["documents"]) if "documents" in results else [],
                "ids": results["ids"] if "ids" in results else []
            }
            
            # Apply post-filtering for special filters
            if special_filters and search_results["metadatas"]:
                filtered_docs = []
                filtered_metas = []
                filtered_distances = []
                filtered_ids = []
                
                for i, meta in enumerate(search_results["metadatas"]):
                    include_item = True
                    
                    # Check each special filter
                    for field, search_term in special_filters.items():
                        field_value = meta.get(field, "")
                        if search_term.lower() not in field_value.lower():
                            include_item = False
                            break
                    
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

@app.get("/rag/metadata", tags=["RAG"])
async def get_rag_metadata():
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

# Graph API Routes
@app.get("/graph/vendors", tags=["Graph"])
async def list_vendors():
    """Get all vendors"""
    try:
        result = run_graph_query("MATCH (v:Vendor) RETURN v.name AS vendor")
        if result is None:
            # Use mock data if Neo4j is not available
            return {"vendors": ["hashicorp", "google", "paloaltonetworks"]}
        return {"vendors": [r["vendor"] for r in result]}
    except Exception as e:
        logging.error(f"Error listing vendors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/products/{vendor}", tags=["Graph"])
async def vendor_products(vendor: str):
    """Get products for a specific vendor"""
    try:
        result = get_vendor_products(vendor)
        if result is None:
            # Use mock data if Neo4j is not available
            mock_data = mock_graph_data()
            return {"products": [r["product"] for r in mock_data["vendor_products"]]}
        return {"products": [r["product"] for r in result]}
    except Exception as e:
        logging.error(f"Error getting vendor products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/vendors/{product}", tags=["Graph"])
async def product_vendors(product: str):
    """Get vendors for a specific product"""
    try:
        result = get_related_vendors(product)
        if result is None:
            # Use mock data if Neo4j is not available
            mock_data = mock_graph_data()
            return {"vendors": [r["vendor"] for r in mock_data["related_vendors"]]}
        return {"vendors": [r["vendor"] for r in result]}
    except Exception as e:
        logging.error(f"Error getting product vendors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/timeline", tags=["Graph"])
async def email_timeline(vendor: Optional[str] = None, product: Optional[str] = None, days: int = 30):
    """Get timeline of emails for a vendor or product"""
    try:
        result = get_email_timeline(vendor, product, days)
        if result is None:
            # Use mock data if Neo4j is not available
            mock_data = mock_graph_data()
            return {"timeline": mock_data["email_timeline"]}
        return {"timeline": result}
    except Exception as e:
        logging.error(f"Error getting email timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/analytics/count/{vendor}", tags=["Graph"])
async def count_emails(vendor: str):
    """Count emails from a specific vendor"""
    try:
        count = count_vendor_emails(vendor)
        return {"vendor": vendor, "email_count": count}
    except Exception as e:
        logging.error(f"Error counting vendor emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/analytics/recent", tags=["Graph"])
async def recent_emails(vendor: Optional[str] = None, days: int = 7):
    """Count recent emails from a vendor"""
    try:
        count = count_recent_emails(vendor, days)
        return {"vendor": vendor or "all", "days": days, "email_count": count}
    except Exception as e:
        logging.error(f"Error counting recent emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/analytics/security", tags=["Graph"])
async def security_emails(days: int = 30):
    """Find security-related emails"""
    try:
        emails = find_security_emails(days)
        return {"days": days, "emails": emails}
    except Exception as e:
        logging.error(f"Error finding security emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/graph/query", tags=["Graph"])
async def custom_graph_query(request: GraphQueryRequest):
    """Run a custom Cypher query"""
    try:
        result = run_graph_query(request.query, request.params)
        if result is None:
            # Return empty result if Neo4j is not available
            return {"results": []}
        return {"results": result}
    except Exception as e:
        logging.error(f"Error running custom query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Debug API Routes
@app.get("/debug/raw_search", tags=["Debug"])
async def raw_search(query: str, limit: int = 10):
    """Perform a raw search without any filtering to debug results"""
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

@app.get("/debug/collection_info", tags=["Debug"])
async def collection_info():
    """Get detailed information about the collection"""
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

@app.get("/debug/test_embedding", tags=["Debug"])
async def test_embedding(text: str = "Test embedding generation"):
    """Test embedding generation to check dimensions"""
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

# Unified Search API Routes
@app.post("/search/unified", tags=["Search"])
async def unified_search_endpoint(query: str, top_k: int = 5):
    """Perform a unified search using both vector and graph capabilities"""
    try:
        # Process the query to extract parameters
        processed = process_search_query(query)
        
        # Perform unified search
        results = unified_search(
            processed["query_text"],
            processed["filters"],
            processed["graph_filters"],
            top_k
        )
        
        # Apply graph-enhanced ranking
        reranked = graph_enhanced_ranking(results, processed["query_text"])
        
        # Format results for API response
        formatted = format_search_results(reranked)
        
        # Add extracted parameters to response
        formatted["extracted_parameters"] = {
            "filters": processed["filters"],
            "graph_filters": processed["graph_filters"]
        }
        
        return formatted
    
    except Exception as e:
        logging.error(f"Error in unified search: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.post("/search/nl", tags=["Search"])
async def natural_language_query(query: str):
    """Process a natural language query and return structured results"""
    try:
        # Process the query
        processed = process_search_query(query)
        query_lower = query.lower()
        
        # Determine query type
        query_type = "search"  # Default
        
        if "how many" in query_lower or "count" in query_lower:
            query_type = "count"
        elif "list" in query_lower or "what products" in query_lower:
            query_type = "list"
        
        # Handle different query types
        if query_type == "count":
            # Count emails
            vendor = processed["filters"].get("vendor")
            days = processed["graph_filters"].get("days", 30)
            
            count = count_recent_emails(vendor, days)
            
            time_period = f"in the past {days} days" if days else ""
            vendor_str = f"from {vendor}" if vendor else ""
            
            answer = f"There are {count} emails {vendor_str} {time_period}."
            
            return {
                "answer": answer.strip(),
                "query_type": "count",
                "parameters": {
                    "vendor": vendor,
                    "days": days
                },
                "data": {
                    "count": count
                }
            }
            
        elif query_type == "list":
            # List products
            vendor = processed["filters"].get("vendor")
            
            if vendor:
                products = get_vendor_products_enhanced(vendor)
                
                return {
                    "answer": f"Found {len(products)} products for {vendor}.",
                    "query_type": "list",
                    "parameters": {
                        "vendor": vendor
                    },
                    "data": {
                        "products": products
                    }
                }
            else:
                return {
                    "answer": "Please specify a vendor to list products.",
                    "query_type": "list",
                    "parameters": {},
                    "data": {}
                }
                
        else:
            # Default to search
            results = unified_search(
                processed["query_text"],
                processed["filters"],
                processed["graph_filters"],
                5
            )
            
            reranked = graph_enhanced_ranking(results, processed["query_text"])
            formatted = format_search_results(reranked)
            
            return {
                "answer": f"Found {len(formatted['results'])} results for your query.",
                "query_type": "search",
                "parameters": processed,
                "data": formatted
            }
    
    except Exception as e:
        logging.error(f"Error processing natural language query: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Check system health"""
    try:
        # Check if ChromaDB is accessible
        collection = llm_utils.get_chroma_collection()
        chroma_count = collection.count()
        
        # Check if Neo4j is accessible
        neo4j_status = "unavailable"
        try:
            result = run_graph_query("RETURN 1 AS test")
            if result and result[0]["test"] == 1:
                neo4j_status = "available"
        except:
            pass
        
        return {
            "status": "healthy", 
            "components": {
                "chromadb": {
                    "status": "available",
                    "document_count": chroma_count
                },
                "neo4j": {
                    "status": neo4j_status
                }
            }
        }
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)