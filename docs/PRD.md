# VendorUpdater Bot - Product Requirements Document (PRD)

## 1. Project Overview

VendorUpdater Bot is a system designed to process vendor emails, extract valuable information, and make it searchable through both vector and graph-based approaches. The system helps users stay informed about vendor updates, product announcements, security alerts, and events.

## 2. System Architecture

### 2.1 Core Components

#### Email Processing Pipeline
- [x] Email harvesting from IMAP or local files
- [x] Text normalization and cleaning
- [x] Metadata extraction and enrichment
- [x] Content classification
- [x] Text chunking and embedding generation
- [x] Dual storage in ChromaDB and Neo4j

#### Query API Layer
- [x] RAG API for vector search
- [x] Graph API for relationship queries
- [ ] Unified API combining both approaches
- [x] Debug API for system inspection

#### User Interface
- [ ] Streamlit-based dashboard for data visualization
- [x] Command-line tools for testing and debugging

## 3. Key Features

### 3.1 Email Processing
- [x] **Email Harvesting**: Fetch emails from IMAP server or read from local directory
- [x] **Text Normalization**: Clean HTML, remove signatures, extract text from attachments
- [x] **Metadata Extraction**: Extract sender, date, language, vendor information
- [x] **Content Classification**: Classify email type and identify products using LLMs
- [x] **Vector Storage**: Store text chunks and embeddings in ChromaDB
- [x] **Graph Storage**: Create nodes and relationships in Neo4j

### 3.2 Search Capabilities
- [x] **Vector Search**: Find relevant content based on semantic similarity
- [x] **Metadata Filtering**: Filter by vendor, product, type, date
- [x] **Graph Queries**: Explore relationships between vendors, products, and emails
- [ ] **Unified Search**: Combine vector and graph approaches for enhanced results
- [ ] **Partial Matching**: Support for partial matching in metadata filters (type, product)
- [ ] **Composite Field Handling**: Better handling of multi-value and composite metadata fields

### 3.3 Analytics
- [x] **Vendor Analysis**: Track email volume by vendor
- [x] **Product Tracking**: Monitor updates for specific products
- [x] **Security Alerts**: Identify security-related communications
- [x] **Timeline Views**: View communications over time

## 4. Technical Requirements

### 4.1 Data Storage
- [x] **ChromaDB**: Store text chunks, embeddings, and metadata
- [x] **Neo4j**: Store graph relationships between entities
- [x] **File System**: Store raw emails and processed text

### 4.2 External Services
- [x] **AWS Bedrock**: Generate embeddings and classifications
- [x] **Email Server**: IMAP access for email retrieval

### 4.3 Performance
- [x] **Processing Speed**: Process emails within 30 seconds
- [ ] **Query Response**: Return search results within 2 seconds
- [ ] **Scalability**: Handle up to 1000 emails per day

## 5. Current Issues and Improvements

### 5.1 Data Quality Issues
- [x] **Vendor-Product Relationships**: Ensure all products are correctly associated with vendors
- [ ] **Data Synchronization**: Address inconsistency between ChromaDB and Neo4j
- [ ] **Email Chunking**: Improve tracking of chunks belonging to the same email
- [ ] **Chunk Relationship Model**: Implement parent-child relationship between chunks and source emails

### 5.2 Validation and Testing
- [x] **Data Quality Analysis**: Regular validation of data integrity
- [x] **Relationship Validation**: Ensure vendor-product relationships are accurate
- [ ] **Search Quality Testing**: Evaluate retrieval performance
- [ ] **Confidence Level Testing**: Add tests for relationship confidence level validation
- [ ] **Pipeline Integration**: Integrate validation as a final step in the processing pipeline

### 5.3 User Experience
- [ ] **Query Interface**: Improve natural language query processing
- [ ] **Result Presentation**: Enhance formatting and organization of search results
- [ ] **Visualization**: Add more graph visualizations for relationship exploration
- [ ] **Fallback Mechanism**: Implement graceful handling of empty results with appropriate fallback strategies

## 6. Development Roadmap

### 6.1 Phase 1: Core Functionality ✅
- [x] Email processing pipeline
- [x] Basic search capabilities
- [x] Initial data storage

### 6.2 Phase 2: Data Quality 🔄
- [x] Fix vendor-product relationships
- [ ] Improve data synchronization
- [x] Enhance validation tools

### 6.3 Phase 3: Enhanced Search 🔄
- [ ] Implement unified search API
- [ ] Improve natural language query processing
- [ ] Add advanced filtering options
- [ ] Enhance date range handling for queries like "recent" and "past week"
- [ ] Implement better type filtering for composite types

### 6.4 Phase 4: Analytics and Reporting 📅
- [ ] Add dashboard for vendor analytics
- [ ] Create automated reports
- [ ] Implement alerting for important updates

### 6.5 Phase 5: Cleanup 📅
- [ ] get rid of unused files and temporary created tools, that are no longer used.
- [ ] Refresh and consolidate all docs

## 7. Success Metrics

- [ ] **Data Accuracy**: >95% correct vendor-product relationships
- [ ] **Search Relevance**: >80% relevant results in top 5 responses
- [x] **Processing Efficiency**: <30 seconds per email
- [ ] **User Satisfaction**: Positive feedback on search quality and result relevance



*** need to be updated:
1. added feature to use a remote chromadb, configured via the config file. - done. add to the prd items and mark as complete.***
2. add humaninthemiddle flag to enable step by step debuggin of all the ingestion and databasing. with each step input and output. to validate data is actually being catagorized correctly. this will base trust for the later query tweaks.