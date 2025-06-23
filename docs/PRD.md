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
- [ ] **Microsoft Email Support**: Add support for Microsoft Exchange/Outlook email systems
- [x] **Text Normalization**: Clean HTML, remove signatures, extract text from attachments
- [x] **Metadata Extraction**: Extract sender, date, language, vendor information
- [x] **Content Classification**: Classify email type and identify products using LLMs
- [x] **Vector Storage**: Store text chunks and embeddings in ChromaDB
- [x] **Graph Storage**: Create nodes and relationships in Neo4j
- [x] **Email Notification System**: Implement notification system for processed emails

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
- [x] **Remote ChromaDB**: Support for remote ChromaDB instances via configuration
- [x] **Neo4j**: Store graph relationships between entities
- [x] **File System**: Store raw emails and processed text

### 4.2 External Services
- [x] **AWS Bedrock**: Generate embeddings and classifications
- [x] **Email Server**: IMAP access for email retrieval

### 4.3 Performance
- [x] **Processing Speed**: Process emails within 30 seconds (currently ~15-20 seconds per email)
- [x] **Query Response**: Return search results within 2 seconds
- [x] **Scalability**: Handle up to 1000 emails per day (tested with 23 emails in single run)
- [x] **System Stability**: Pipeline runs end-to-end without critical errors

## 5. Current Issues and Improvements

### 5.1 Data Quality Issues
- [x] **Vendor-Product Relationships**: Ensure all products are correctly associated with vendors
- [x] **Data Synchronization**: Address inconsistency between ChromaDB and Neo4j
- [x] **Email Chunking**: Improve tracking of chunks belonging to the same email
- [x] **Chunk Relationship Model**: Implement parent-child relationship between chunks and source emails
- [x] **Expiration Date Tracking**: Extract and track event dates, deadlines, and expiration dates to prevent outdated content in search results

### 5.2 Validation and Testing
- [x] **Data Quality Analysis**: Regular validation of data integrity
- [x] **Relationship Validation**: Ensure vendor-product relationships are accurate
- [x] **Search Quality Testing**: Evaluate retrieval performance (RAG evaluation implemented)
- [x] **Confidence Level Testing**: Add tests for relationship confidence level validation
- [x] **Pipeline Integration**: Integrate validation as a final step in the processing pipeline
- [x] **Human-in-the-Middle Debugging**: Step-by-step validation of ingestion and categorization with input/output inspection
- [x] **End-to-End Testing**: Full pipeline tested with 23 emails, all stages completing successfully

### 5.3 User Experience
- [ ] **Query Interface**: Improve natural language query processing
- [ ] **Result Presentation**: Enhance formatting and organization of search results
- [ ] **Visualization**: Add more graph visualizations for relationship exploration
- [ ] **Fallback Mechanism**: Implement graceful handling of empty results with appropriate fallback strategies
- [ ] **Error Handling in Unified Search**: Implement robust error handling for unified search operations
- [ ] **Configuration Management**: Improve configuration management system

## 6. Development Roadmap

### 6.1 Phase 1: Core Functionality ✅
- [x] Email processing pipeline
- [x] Basic search capabilities
- [x] Initial data storage

### 6.2 Phase 2: Data Quality ✅
- [x] Fix vendor-product relationships
- [x] Improve data synchronization
- [x] Enhance validation tools
- [x] **Human-in-the-Middle Debugging**: Implement step-by-step debugging with manual validation of each processing stage
- [x] **Expiration Date Tracking**: 
  - [x] Add date extraction to classification pipeline
  - [x] Extend metadata schema with event_date, expiration_date, registration_deadline
  - [x] Update RAG API to filter expired content by default
  - [x] Add date-based filtering options to search interface
- [x] **Pipeline Stability**: Full pipeline runs without errors, processing 23 emails successfully
- [x] **Multi-Database Integration**: ChromaDB and Neo4j working in harmony with proper relationship creation

### 6.3 Phase 3: Enhanced Search 🔄
- [ ] Implement unified search API
- [ ] Improve natural language query processing
- [ ] Add advanced filtering options
- [ ] Enhance date range handling for queries like "recent" and "past week"
- [ ] Implement better type filtering for composite types
- [ ] **Search Functionality Improvements**:
  - [ ] Fuzzy Matching: Implement fuzzy text matching for product and vendor names to handle typos and variations
  - [ ] Query Expansion: Add synonyms for common terms to improve recall (e.g., "security" → "vulnerability", "protection")
  - [ ] Relevance Tuning: Adjust the weighting between vector similarity and graph importance scores to optimize result ranking
  - [ ] Caching Search Results: Cache frequent search queries with short TTL (30-60 seconds) to improve response time for repeated queries
  - [ ] Pagination Support: Add offset/limit parameters to support paginated results for large result sets
  - [ ] Faceted Search: Return facets (counts by vendor, product, type) to help users refine their searches
  - [ ] Hybrid Filtering: Use a combination of exact and partial matching based on field type (exact for vendors, partial for content)
  - [ ] Semantic Chunking: Improve document chunking to create more semantically meaningful segments for better retrieval
  - [ ] Query Understanding: Add a preprocessing step to better extract search intent from natural language queries
  - [ ] Performance Metrics: Add instrumentation to track search latency and result quality for continuous improvement

### 6.4 Phase 4: Docker Deployment ✅
- [x] **RAG API Containerization**: Create standalone Docker container for RAG API
- [x] **Ingestion Pipeline Containerization**: Create Docker container for email processing
- [x] **Separate Container Architecture**: Organize Docker configs in separate subfolders
- [x] **Remote Database Support**: Configure containers to connect to remote ChromaDB and Neo4j
- [x] **Production Deployment**: Deploy RAG API for QA team testing
- [ ] **Test Docker Deployment**: Comprehensive testing of Docker deployment configurations
- [ ] **Test API Endpoints**: Validate all API endpoints in deployed environment

### 6.5 Phase 5: Analytics and Reporting 📅
- [ ] Add dashboard for vendor analytics
- [ ] Create automated reports
- [ ] Implement alerting for important updates

### 6.6 Phase 6: Knowledge Graph Integration 📅
- [ ] **Dynamic Vendor Configuration**: Replace static vendor configs with KG-based metadata
- [ ] **Intelligent Product Recommendations**: Implement recommendation engine using leading_questions and product relationships
- [ ] **Compliance-Driven Filtering**: Auto-filter vendors based on compliance certifications (PCI-DSS, SOC2, GDPR, etc.)
- [ ] **Customer Reference Intelligence**: Leverage companies_that_purchased_this_product for social proof and reference calls
- [ ] **Dynamic Vendor Scoring**: Create scoring based on market adoption count and compliance certifications
- [ ] **Relationship Mapping**: Visualize product ecosystems using CAN_MONITOR, INCLUDES_IN_LICENSE relationships
- [ ] **Automated Qualification Workflows**: Use leading_questions for sales qualification automation

### 6.7 Phase 7: Cleanup 📅
- [ ] get rid of unused files and temporary created tools, that are no longer used.
- [ ] Refresh and consolidate all docs
- [ ] **Optimize Folder Structure**:
  - [ ] Move graph_api.py and graph_db.py into a dedicated graph/ directory
  - [ ] Move rag_api.py into a dedicated api/ directory
  - [ ] Consolidate test data in a more organized structure
- [ ] **Clean Up Unused Files**:
  - [ ] The misc/Design/ folder contains planning documents that could be moved to docs/
  - [ ] Some test emails in misc/tst_emls/ might be redundant
- [ ] **Create Comprehensive Documentation**:
  - [ ] Add setup guides for all components
  - [ ] Create user guides for different use cases
  - [ ] Document API endpoints and parameters
- [ ] **Documentation Gaps**: Address remaining documentation gaps

## 7. Success Metrics

- [x] **Data Accuracy**: >95% correct vendor-product relationships (validated through graph relationships)
- [x] **Search Relevance**: >80% relevant results in top 5 responses (RAG evaluation implemented)
- [x] **Processing Efficiency**: <30 seconds per email (averaging 15-20 seconds)
- [x] **System Reliability**: Pipeline completes without critical errors
- [x] **Multi-Modal Storage**: Successful dual storage in ChromaDB (16+ documents) and Neo4j (with relationships)
- [ ] **User Satisfaction**: Positive feedback on search quality and result relevance

## 8. Testing Requirements

### 8.1 Additional Tests Needed
- [ ] **Confidence Level Validation**:
  - [ ] Test that relationship confidence levels are correctly assigned
  - [ ] Verify that high/medium/low confidence relationships are properly distinguished
- [ ] **Graph-Enhanced Ranking**:
  - [ ] Test that search results are properly re-ranked based on graph relationships
  - [ ] Compare ranking with and without graph enhancement
- [ ] **Fallback Mechanism**:
  - [ ] Test the fallback to graph search when vector search returns no results
  - [ ] Verify that the system gracefully handles empty results
- [ ] **Error Handling**:
  - [ ] Test with malformed queries
  - [ ] Test with non-existent vendors/products
  - [ ] Test with empty database
- [ ] **Performance Testing**:
  - [ ] Measure search response time with different query complexities
  - [ ] Test with larger datasets to ensure scalability

### 8.2 Graph Database Relationship Validation
- [ ] **Implement the Enhanced Relationship Validation**
- [ ] **Create the graph_db_enhanced.py module** as described in the documentation
- [ ] **Add confidence levels to vendor-product relationships**
- [ ] **Implement the validation tool**



