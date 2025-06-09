Current Search Implementation: (9.6)
Currently, the search functionality is split across two systems:

Vector Search (src/hybrid_search.py):
    Uses embeddings for semantic similarity
    Supports metadata filtering
    Returns documents ranked by vector similarity
Graph Search (graph_db.py):
    Uses Cypher queries for relationship exploration
    Supports analytical queries (counts, timelines)
    Returns structured data about relationships

Deep Dive into Search Steps
Vector Search Flow:
    User submits a query text and optional metadata filters
    Query text is embedded using AWS Bedrock Titan
    ChromaDB performs similarity search with metadata filtering
    Results are ranked by vector similarity
    Top-k results are returned with their metadata

def hybrid_search(query_text, metadata_filters=None, top_k=5):
    collection = llm_utils.get_chroma_collection()
    
    # Convert metadata filters to ChromaDB where clause
    where_clause = None
    if metadata_filters:
        where_clause = metadata_filters if len(metadata_filters) == 1 else {
            "$and": [{k: v} for k, v in metadata_filters.items()]
        }
    
    # Get embedding for query
    query_embedding = llm_utils.embed_text_titan(query_text)
    
    # Execute search with filters
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_clause
    )
    
    return {
        "documents": results["documents"][0],
        "metadatas": results["metadatas"][0],
        "distances": results["distances"][0],
        "ids": results["ids"][0]
    }


Graph Search Flow:
    User submits a Cypher query or uses a predefined function
    Neo4j executes the query against the graph database
    Results show relationships between vendors, products, and emails

def get_email_timeline(vendor_name=None, product_name=None, days=30):
    params = {"days": days}
    where_clause = ""
    
    if vendor_name:
        where_clause += "v.name = $vendor"
        params["vendor"] = vendor_name
    
    if product_name:
        if where_clause:
            where_clause += " AND "
        where_clause += "p.name = $product"
        params["product"] = product_name
    
    if where_clause:
        where_clause = "WHERE " + where_clause
    
    query = f"""
    MATCH (e:Email)-[:FROM]->(v:Vendor), (e)-[:ABOUT]->(p:Product)
    {where_clause}
    RETURN e.id AS email_id, e.date AS date, e.type AS type, 
           v.name AS vendor, p.name AS product
    ORDER BY e.date DESC
    LIMIT 10
    """
    return run_graph_query(query, params)


Best Practice Approach for Hybrid Search
To create a truly hybrid search that combines vector similarity, metadata filtering, and graph relationships, I recommend the following approach:

1. Create a Unified Search API
def unified_search(query_text, filters=None, graph_filters=None, top_k=5):
    """
    Unified search combining vector search and graph relationships
    
    Args:
        query_text: The search query text
        filters: Dict of metadata filters for vector search
        graph_filters: Dict of graph filters (vendor, product, type, date range)
        top_k: Number of results to return
    
    Returns:
        Dict with search results and related entities
    """
    # Step 1: Vector search with metadata filters
    vector_results = hybrid_search(query_text, filters, top_k)
    
    # Step 2: Extract email IDs from vector results
    email_ids = []
    for meta in vector_results["metadatas"]:
        if "email_id" in meta and meta["email_id"] not in email_ids:
            email_ids.append(meta["email_id"])
    
    # Step 3: Find related entities in graph database
    related_entities = {}
    if email_ids:
        # Find related products
        products_query = """
        MATCH (e:Email)-[:ABOUT]->(p:Product)
        WHERE e.id IN $email_ids
        RETURN p.name AS product, count(e) AS count
        ORDER BY count DESC
        """
        related_entities["products"] = run_graph_query(products_query, {"email_ids": email_ids})
        
        # Find related vendors
        vendors_query = """
        MATCH (e:Email)-[:FROM]->(v:Vendor)
        WHERE e.id IN $email_ids
        RETURN v.name AS vendor, count(e) AS count
        ORDER BY count DESC
        """
        related_entities["vendors"] = run_graph_query(vendors_query, {"email_ids": email_ids})
    
    # Step 4: Combine and return results
    return {
        "documents": vector_results["documents"],
        "metadatas": vector_results["metadatas"],
        "related_entities": related_entities
    }


2. Add Graph-Enhanced Ranking
def graph_enhanced_ranking(results, query_text):
    """
    Enhance search ranking using graph relationships
    
    Args:
        results: Results from vector search
        query_text: Original query text
    
    Returns:
        Reranked results
    """
    # Extract email IDs and document scores
    email_scores = {}
    for i, meta in enumerate(results["metadatas"]):
        email_id = meta.get("email_id")
        if email_id:
            if email_id not in email_scores:
                email_scores[email_id] = results["distances"][i]
            else:
                # Keep the highest score for each email
                email_scores[email_id] = max(email_scores[email_id], results["distances"][i])
    
    # Get graph importance scores
    graph_scores = {}
    if email_scores:
        query = """
        MATCH (e:Email)
        WHERE e.id IN $email_ids
        OPTIONAL MATCH (e)-[:ABOUT]->(p:Product)
        OPTIONAL MATCH (e)-[:FROM]->(v:Vendor)
        WITH e, count(p) AS product_count, v
        RETURN e.id AS email_id, product_count, v.name AS vendor
        """
        graph_results = run_graph_query(query, {"email_ids": list(email_scores.keys())})
        
        for result in graph_results:
            email_id = result["email_id"]
            # Simple graph score based on product mentions
            graph_scores[email_id] = result["product_count"] * 0.1
    
    # Combine vector and graph scores
    combined_scores = {}
    for email_id, score in email_scores.items():
        graph_score = graph_scores.get(email_id, 0)
        combined_scores[email_id] = score + graph_score
    
    # Rerank results
    reranked_results = {
        "documents": [],
        "metadatas": [],
        "distances": [],
        "ids": []
    }
    
    # Sort by combined score
    sorted_emails = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Rebuild results in new order
    for email_id, _ in sorted_emails:
        for i, meta in enumerate(results["metadatas"]):
            if meta.get("email_id") == email_id:
                reranked_results["documents"].append(results["documents"][i])
                reranked_results["metadatas"].append(results["metadatas"][i])
                reranked_results["distances"].append(results["distances"][i])
                reranked_results["ids"].append(results["ids"][i])
    
    return reranked_results


3. Create a Natural Language Interface
def process_search_query(query):
    """
    Process natural language query and extract search parameters
    
    Args:
        query: Natural language query
    
    Returns:
        Dict with query text and filters
    """
    # Extract time constraints
    time_filter = None
    if "past week" in query.lower():
        time_filter = 7
    elif "past month" in query.lower():
        time_filter = 30
    
    # Extract vendor constraints
    vendor_filter = None
    vendor_match = re.search(r"from\s+(\w+)", query.lower())
    if vendor_match:
        vendor_filter = vendor_match.group(1)
    
    # Extract product constraints
    product_filter = None
    product_match = re.search(r"about\s+(\w+)", query.lower())
    if product_match:
        product_filter = product_match.group(1)
    
    # Extract type constraints
    type_filter = None
    if "security" in query.lower():
        type_filter = "security"
    elif "webinar" in query.lower():
        type_filter = "webinar"
    
    # Build filters
    filters = {}
    if vendor_filter:
        filters["vendor"] = vendor_filter
    if product_filter:
        filters["product"] = product_filter
    if type_filter:
        filters["type"] = type_filter
    
    # Build graph filters
    graph_filters = {}
    if time_filter:
        graph_filters["days"] = time_filter
    
    return {
        "query_text": query,
        "filters": filters,
        "graph_filters": graph_filters
    }


This approach combines the strengths of both vector search and graph search to provide more relevant and contextually rich results. The unified_search function first performs a vector search, then enriches the results with related entities from the graph database. The graph_enhanced_ranking function uses graph relationships to improve the ranking of search results.

please implement this in a test file first and put it in /Tests/tools/unified_search.py

we will play with it, and once it fully baked, we will integrate it to the app, so keep in mind that it should be ready for a lift-and-shift, or at least compatible with the current app.