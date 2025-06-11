"""
Multi-value search implementation for VendorUpdater_Bot

This module extends hybrid search to support multiple values for metadata filters.
"""

import logging
from typing import Dict, List, Any, Optional
from src import llm_utils
from src.hybrid_search import hybrid_search

def multi_value_search(query_text: str, filters: Optional[Dict[str, List[str]]] = None, top_k: int = 5) -> Dict[str, Any]:
    """
    Perform search with support for multiple values per filter field
    
    Args:
        query_text: The search query text
        filters: Dict of metadata filters where values are lists of acceptable values
        top_k: Number of results to return
    
    Returns:
        Dict with search results
    """
    collection = llm_utils.get_chroma_collection()
    logging.info(f"Collection has {collection.count()} documents")
    
    # Generate embedding for the query
    query_embedding = llm_utils.embed_text_titan(query_text)
    logging.info(f"Generated embedding with dimension: {len(query_embedding)}")
    
    # If no multi-value filters, just use regular search
    if not filters:
        return hybrid_search(query_text, None, top_k)
    
    # Get more results initially for post-filtering
    expanded_top_k = top_k * 5
    
    # Perform vector search without filters first
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=expanded_top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format initial results
        formatted_results = {
            "documents": results["documents"][0] if results["documents"] and len(results["documents"]) > 0 else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] and len(results["metadatas"]) > 0 else [],
            "distances": results["distances"][0] if results["distances"] and len(results["distances"]) > 0 else [],
            "ids": results["ids"][0] if results["ids"] and len(results["ids"]) > 0 else []
        }
        
        # Apply multi-value filtering
        filtered_indices = []
        for i, metadata in enumerate(formatted_results["metadatas"]):
            include_item = True
            
            # Check each filter field
            for field, values in filters.items():
                if field not in metadata:
                    include_item = False
                    break
                
                # For multi-value fields in metadata (comma-separated)
                if isinstance(metadata[field], str) and "," in metadata[field]:
                    metadata_values = [v.strip().lower() for v in metadata[field].split(",")]
                    
                    # Check if any of the filter values match any of the metadata values
                    field_match = False
                    for filter_value in values:
                        for meta_value in metadata_values:
                            if filter_value.lower() in meta_value:
                                field_match = True
                                break
                        if field_match:
                            break
                    
                    if not field_match:
                        include_item = False
                        break
                
                # For single-value fields in metadata
                else:
                    meta_value = str(metadata[field]).lower()
                    
                    # Check if any of the filter values match
                    field_match = False
                    for filter_value in values:
                        if filter_value.lower() in meta_value:
                            field_match = True
                            break
                    
                    if not field_match:
                        include_item = False
                        break
            
            if include_item:
                filtered_indices.append(i)
        
        # Apply the filter
        if filtered_indices:
            filtered_results = {
                "documents": [formatted_results["documents"][i] for i in filtered_indices][:top_k],
                "metadatas": [formatted_results["metadatas"][i] for i in filtered_indices][:top_k],
                "distances": [formatted_results["distances"][i] for i in filtered_indices][:top_k],
                "ids": [formatted_results["ids"][i] for i in filtered_indices][:top_k]
            }
            
            logging.info(f"Multi-value search returned {len(filtered_results['documents'])} results")
            return filtered_results
        else:
            logging.warning("No results match the multi-value filters")
            return {
                "documents": [],
                "metadatas": [],
                "distances": [],
                "ids": []
            }
    
    except Exception as e:
        logging.error(f"Multi-value search failed: {e}")
        # Return empty results on error
        return {
            "documents": [],
            "metadatas": [],
            "distances": [],
            "ids": []
        }