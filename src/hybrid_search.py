"""
Hybrid search implementation for VendorUpdater_Bot

This module combines vector search with metadata filtering.
"""

import logging
from typing import Dict, List, Any, Optional
from src import llm_utils

def hybrid_search(query_text: str, filters: Optional[Dict[str, Any]] = None, top_k: int = 5) -> Dict[str, Any]:
    """
    Perform hybrid search using vector similarity and metadata filtering
    
    Args:
        query_text: The search query text
        filters: Dict of metadata filters
        top_k: Number of results to return
    
    Returns:
        Dict with search results
    """
    collection = llm_utils.get_chroma_collection()
    logging.info(f"Collection has {collection.count()} documents")
    
    # Generate embeddings using the correct model
    try:
        # Get embedding for the query
        query_embedding = llm_utils.embed_text_titan(query_text)
        logging.info(f"Generated embedding with dimension: {len(query_embedding)}")
        
        # Process filters
        where_clause = None
        if filters:
            # ChromaDB expects filters in a specific format
            # For multiple conditions, we need to use $and operator
            if len(filters) > 1:
                where_clause = {"$and": []}
                for key, value in filters.items():
                    where_clause["$and"].append({key: value})
            else:
                # For a single condition, we can use it directly
                where_clause = filters
            logging.info(f"Using where clause: {where_clause}")
        
        # Perform vector search with metadata filtering
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = {
            "documents": results["documents"][0] if results["documents"] and len(results["documents"]) > 0 else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] and len(results["metadatas"]) > 0 else [],
            "distances": results["distances"][0] if results["distances"] and len(results["distances"]) > 0 else [],
            "ids": results["ids"][0] if results["ids"] and len(results["ids"]) > 0 else []
        }
        
        logging.info(f"Search returned {len(formatted_results['documents'])} results")
        return formatted_results
    except Exception as e:
        logging.error(f"Search failed: {e}")
        # Return empty results on error
        return {
            "documents": [],
            "metadatas": [],
            "distances": [],
            "ids": []
        }