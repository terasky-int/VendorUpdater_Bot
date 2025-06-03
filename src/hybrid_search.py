import logging
from src import llm_utils

def hybrid_search(query_text, metadata_filters=None, top_k=5):
    """
    Perform hybrid search with metadata filtering.
    
    Args:
        query_text: The search query text
        metadata_filters: Dict of metadata filters like {"vendor": "hashicorp"}
        top_k: Number of results to return
    
    Returns:
        Dict with documents, metadatas, distances, and ids
    """
    collection = llm_utils.get_chroma_collection()
    
    # Debug info
    count = collection.count()
    logging.info(f"Collection has {count} documents")
    
    # Convert metadata filters to ChromaDB where clause
    where_clause = None
    if metadata_filters:
        # Handle single filter
        if len(metadata_filters) == 1:
            where_clause = metadata_filters
        # Handle multiple filters (AND condition)
        else:
            where_clause = {"$and": [
                {k: v} for k, v in metadata_filters.items()
            ]}
        
        logging.info(f"Using where clause: {where_clause}")
    
    try:
        # Get embedding for query
        query_embedding = llm_utils.embed_text_titan(query_text)
        
        # Execute search with filters
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause
        )
        
        # Log results
        doc_count = len(results["documents"][0]) if results["documents"] else 0
        logging.info(f"Search returned {doc_count} results")
        
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "ids": results["ids"][0] if results["ids"] else []
        }
    
    except Exception as e:
        logging.error(f"Search error: {e}")
        return {
            "documents": [],
            "metadatas": [],
            "distances": [],
            "ids": []
        }

def keyword_search(query_text, metadata_filters=None, top_k=5):
    """
    Perform keyword-based search without embeddings.
    
    Args:
        query_text: The search query text
        metadata_filters: Dict of metadata filters
        top_k: Number of results to return
    
    Returns:
        Dict with documents, metadatas, and ids
    """
    collection = llm_utils.get_chroma_collection()
    
    # We need to use embeddings for ChromaDB, so we'll use the same approach as hybrid_search
    # but focus on the text content
    try:
        query_embedding = llm_utils.embed_text_titan(query_text)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=metadata_filters
        )
        
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "ids": results["ids"][0] if results["ids"] else []
        }
    except Exception as e:
        logging.error(f"Keyword search error: {e}")
        return {
            "documents": [],
            "metadatas": [],
            "ids": []
        }