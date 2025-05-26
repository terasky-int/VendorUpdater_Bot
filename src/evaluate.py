from src import vector_search

def run_rag_test(email_id, chunks, config):
    # Example hardcoded QA for demonstration
    test_queries = [
        "Who is the vendor?",
        "What product is mentioned?",
        "What is the date of the event or bulletin?"
    ]
    print(f"🧪 RAG Evaluation for Email ID {email_id}")
    for query in test_queries:
        result = vector_search.query(query, top_k=1)
        print(f"Q: {query}\nA: {result}\n")