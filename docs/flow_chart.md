# VendorUpdater_Bot Flow Chart

```mermaid
graph TD
    %% Email Processing Pipeline
    subgraph "Email Processing Pipeline (Cron Job)"
        A[IMAP Server / Local Files] -->|Fetch Emails| B[Email Harvester]
        B -->|Raw Emails| C[Normalizer]
        C -->|Clean Text| D[Enricher]
        D -->|Metadata| E[Classifier]
        E -->|Labeled Data| F[Chunker]
        F -->|Text Chunks| G[Embedder]
        G -->|Embeddings| H[Indexer]
        
        H -->|Store| I[(ChromaDB)]
        H -->|Store| J[(Neo4j)]
        
        K[Monitoring] -.->|Log| L[Logs/Metrics]
    end
    
    %% API Layer
    subgraph "API Layer"
        M[RAG API] -->|Vector Search| I
        N[Graph API] -->|Graph Query| J
        O[Unified API] -->|Hybrid Search| P{Search Orchestrator}
        P -->|Vector Query| I
        P -->|Graph Query| J
    end
    
    %% External Agent
    subgraph "External AI Agent"
        Q[User Query] -->|Natural Language| R[Query Processor]
        R -->|Structured Query| S[API Client]
        S -->|HTTP Request| T{API Endpoint}
        T -->|Vector Search| M
        T -->|Graph Query| N
        T -->|Hybrid Search| O
        
        U[Results] -->|Format Response| V[User Response]
    end
    
    %% Data Flow
    I -.->|Results| M
    J -.->|Results| N
    M -.->|Response| T
    N -.->|Response| T
    O -.->|Response| T
    
    %% Styling
    classDef pipeline fill:#f9f,stroke:#333,stroke-width:2px;
    classDef storage fill:#bbf,stroke:#333,stroke-width:2px;
    classDef api fill:#bfb,stroke:#333,stroke-width:2px;
    classDef agent fill:#fbb,stroke:#333,stroke-width:2px;
    
    class A,B,C,D,E,F,G,H,K pipeline;
    class I,J,L storage;
    class M,N,O,P api;
    class Q,R,S,T,U,V agent;
```

## Flow Description

1. **Email Processing Pipeline** (runs as a cron job):
   - Harvests emails from IMAP server or local files
   - Normalizes and cleans the email content
   - Enriches with metadata and classifies content
   - Chunks text and generates embeddings
   - Stores data in both ChromaDB (vector store) and Neo4j (graph database)
   - Monitors performance and logs metrics

2. **API Layer** (provides query endpoints):
   - RAG API: Handles vector search queries using ChromaDB
   - Graph API: Handles relationship queries using Neo4j
   - Unified API: Combines both approaches for enhanced results

3. **External AI Agent** (runs in separate pod):
   - Processes user queries in natural language
   - Converts to structured queries for the API
   - Sends HTTP requests to the appropriate endpoint
   - Formats and presents results to the user

The main endpoint for the external AI agent to use is the `/query` endpoint in the RAG API (`rag_api.py`). This endpoint accepts a JSON payload with:
- `query`: The search query text
- `metadata_filters`: Optional filters for vendor, product, type, etc.
- `top_k`: Number of results to return

For more advanced relationship queries, the agent can use the Graph API endpoints or the future Unified API endpoint that will combine both vector and graph search capabilities.