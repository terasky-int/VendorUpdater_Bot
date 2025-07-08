# Repository Split Plan - Product Requirements Document (PRD)

## Executive Summary

This document outlines the plan to split the current monolithic VendorUpdater_Bot repository into two standalone repositories:
1. **vendor_updater_bot** - Email ingestion and processing agent
2. **TeraskyRag** - RAG (Retrieval-Augmented Generation) system for data querying

## Current State Analysis

### Repository Overview
The current repository contains two main applications that are tightly coupled:
- **Email Processing Pipeline**: Harvests, normalizes, classifies, and indexes vendor emails
- **Query/Search System**: Provides vector search, graph queries, and RAG capabilities

### Key Issues with Current Structure
- Mixed responsibilities in single codebase
- Difficult to scale components independently  
- Complex deployment and maintenance
- Unclear separation of concerns

## Target Architecture

### Repository 1: vendor_updater_bot (Ingestion Agent)

**Purpose**: Process incoming emails and store structured data

**Core Responsibilities**:
- Email harvesting from IMAP servers
- Text normalization and cleaning
- Metadata extraction and enrichment
- Content classification using LLMs
- Text chunking and embedding generation
- Data storage in ChromaDB and Neo4j

**Key Components**:
```
vendor_updater_bot/
├── src/
│   ├── harvest.py              # Email harvesting
│   ├── normalize.py            # Text cleaning
│   ├── enrich.py              # Metadata extraction
│   ├── classify.py            # Content classification
│   ├── chunker.py             # Text chunking
│   ├── embedder.py            # Embedding generation
│   ├── indexer.py             # Data indexing
│   └── llm_utils.py           # LLM utilities
├── main.py                    # Main pipeline
├── config/config.yaml         # Ingestion config
└── docker/                    # Containerization
```

### Repository 2: TeraskyRag (RAG System)

**Purpose**: Provide search and query capabilities over processed data

**Core Responsibilities**:
- Vector similarity search
- Graph database queries
- Unified search combining multiple approaches
- Natural language query processing
- REST API for external integration

**Key Components**:
```
TeraskyRag/
├── src/
│   ├── vector_search.py       # Vector search
│   ├── hybrid_search.py       # Hybrid search
│   ├── unified_search.py      # Unified search
│   └── nl_query_processor.py  # NL processing
├── api/
│   ├── rag_api.py            # Main RAG API
│   ├── unified_api.py        # Unified API
│   └── debug_api.py          # Debug API
├── graph/
│   ├── graph_db.py           # Graph operations
│   └── graph_api.py          # Graph API
└── config/config-rag.yaml    # RAG config
```

## Detailed File Organization

### vendor_updater_bot Structure
```
vendor_updater_bot/
├── config/
│   └── config.yaml                    # Ingestion-specific config
├── data/                              # Data storage directories
│   ├── raw_emails/
│   ├── clean_text/
│   └── eval/
├── src/                               # Core ingestion modules
│   ├── harvest.py                     # Email harvesting from IMAP
│   ├── normalize.py                   # Text cleaning and normalization
│   ├── enrich.py                      # Metadata extraction
│   ├── classify.py                    # Content classification using LLM
│   ├── chunker.py                     # Text chunking
│   ├── embedder.py                    # Embedding generation
│   ├── indexer.py                     # Data indexing to ChromaDB/Neo4j
│   ├── llm_utils.py                   # LLM utilities
│   ├── local_loader.py                # Local email file loading
│   ├── manifest.py                    # Processing manifest
│   ├── monitoring.py                  # System monitoring
│   ├── pipeline_tracker.py            # Pipeline tracking
│   ├── email_notifications.py         # Email notifications
│   ├── human_debug.py                 # Human-in-the-loop debugging
│   └── config_utils.py                # Configuration utilities
├── tests/                             # Ingestion-specific tests
│   ├── unit/
│   │   ├── test_normalize.py
│   │   └── test_enrich.py
│   ├── integration/
│   └── tools/
│       ├── import_all_emails.py
│       ├── reset_databases.py
│       └── test_connection_pooling.py
├── docker/                            # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── docs/                              # Ingestion documentation
│   ├── email_notifications.md
│   ├── human_debug_guide.md
│   └── ingestion_pipeline.md
├── misc/                              # Test data and design docs
│   ├── tst_emls/                      # Test email files
│   └── Design/
├── logs/                              # Log files
├── main.py                            # Main ingestion pipeline
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### TeraskyRag Structure
```
TeraskyRag/
├── config/
│   └── config-rag.yaml               # RAG-specific configuration
├── src/                              # Core RAG modules
│   ├── vector_search.py              # Vector search implementation
│   ├── hybrid_search.py              # Hybrid search (vector + metadata)
│   ├── unified_search.py             # Unified search combining all approaches
│   ├── optimized_search.py           # Performance-optimized search
│   ├── multi_search.py               # Multi-modal search
│   ├── nl_query_processor.py         # Natural language query processing
│   ├── search_benchmark.py           # Search performance benchmarking
│   ├── llm_utils.py                  # LLM utilities (duplicated)
│   ├── config_utils.py               # Configuration utilities (duplicated)
│   └── evaluate.py                   # RAG evaluation
├── api/                              # API layer
│   ├── rag_api.py                    # Main RAG API
│   ├── unified_api.py                # Unified API combining all endpoints
│   ├── debug_api.py                  # Debug and inspection API
│   └── api_endpoints.py              # Additional API endpoints
├── graph/                            # Graph database functionality
│   ├── graph_db.py                   # Graph database operations
│   ├── graph_db_consolidated.py      # Enhanced graph operations
│   └── graph_api.py                  # Graph API endpoints
├── tests/                            # RAG-specific tests
│   ├── unit/
│   ├── integration/
│   │   └── test_enhanced_integration.py
│   └── tools/
│       ├── debug_search.py
│       ├── test_search_quality.py
│       ├── rag_answers.py
│       ├── test_rag_api.py
│       ├── unified_search_api.py
│       ├── unified_search.py
│       ├── nl_query_enhanced.py
│       ├── nl_query.py
│       ├── cypher_query.py
│       ├── simple_query.py
│       ├── show_all_data.py
│       ├── test_analytics.py
│       ├── global_query_eval.py
│       └── vendor_products.py
├── ui/                               # User interface components
│   └── streamlit/
│       ├── inspect_db_pandas.py
│       └── inspect_db_ui.py
├── docker/                           # Docker configuration
│   ├── rag-api/
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── requirements-rag.txt
│   └── README.md
├── docs/                             # RAG documentation
│   ├── api_reference.md
│   ├── api_spec.json
│   ├── graph_database.md
│   ├── graph_db_README.md
│   ├── README_unified_api.md
│   ├── README_unified_search.md
│   ├── search_optimization.md
│   ├── search_strategy.md
│   └── overall_test.md
├── exports/                          # Data exports
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## File Migration Matrix

### Files Moving to vendor_updater_bot
| Current Location | New Location | Notes |
|------------------|--------------|-------|
| `src/harvest.py` | `src/harvest.py` | Email harvesting |
| `src/normalize.py` | `src/normalize.py` | Text normalization |
| `src/enrich.py` | `src/enrich.py` | Metadata extraction |
| `src/classify.py` | `src/classify.py` | Content classification |
| `src/chunker.py` | `src/chunker.py` | Text chunking |
| `src/embedder.py` | `src/embedder.py` | Embedding generation |
| `src/indexer.py` | `src/indexer.py` | Data indexing |
| `src/local_loader.py` | `src/local_loader.py` | Local file loading |
| `src/manifest.py` | `src/manifest.py` | Processing manifest |
| `src/monitoring.py` | `src/monitoring.py` | System monitoring |
| `src/pipeline_tracker.py` | `src/pipeline_tracker.py` | Pipeline tracking |
| `src/email_notifications.py` | `src/email_notifications.py` | Email notifications |
| `src/human_debug.py` | `src/human_debug.py` | Debug interface |
| `main.py` | `main.py` | Main pipeline |
| `misc/tst_emls/` | `misc/tst_emls/` | Test email files |

### Files Moving to TeraskyRag
| Current Location | New Location | Notes |
|------------------|--------------|-------|
| `src/hybrid_search.py` | `src/hybrid_search.py` | Hybrid search |
| `src/unified_search.py` | `src/unified_search.py` | Unified search |
| `src/optimized_search.py` | `src/optimized_search.py` | Optimized search |
| `src/multi_search.py` | `src/multi_search.py` | Multi-modal search |
| `src/vector_search.py` | `src/vector_search.py` | Vector search |
| `src/nl_query_processor.py` | `src/nl_query_processor.py` | NL processing |
| `src/search_benchmark.py` | `src/search_benchmark.py` | Benchmarking |
| `src/evaluate.py` | `src/evaluate.py` | RAG evaluation |
| `rag_api.py` | `api/rag_api.py` | Main RAG API |
| `unified_api.py` | `api/unified_api.py` | Unified API |
| `debug_api.py` | `api/debug_api.py` | Debug API |
| `graph_api.py` | `graph/graph_api.py` | Graph API |
| `graph_db.py` | `graph/graph_db.py` | Graph operations |
| `graph_db_consolidated.py` | `graph/graph_db_consolidated.py` | Enhanced graph ops |
| `ui/streamlit/` | `ui/streamlit/` | UI components |

### Files to Duplicate
| File | Reason for Duplication |
|------|------------------------|
| `src/llm_utils.py` | Both systems need LLM utilities |
| `src/config_utils.py` | Configuration management needed by both |
| `.env.example` | Environment template for both systems |

### Files to Split
| Current File | Split Into | Notes |
|--------------|------------|-------|
| `config/config.yaml` | `vendor_updater_bot/config/config.yaml` + `TeraskyRag/config/config-rag.yaml` | Separate configs |
| `requirements.txt` | Two separate requirements files | Based on actual dependencies |
| `Docker/` | Separate Docker configs | Independent containerization |

## Integration Architecture

### Database Connections
Both repositories connect to shared databases:

**ChromaDB (Vector Storage)**:
- **vendor_updater_bot**: Read/Write access for data ingestion
- **TeraskyRag**: Read-only access for search operations

**Neo4j (Graph Database)**:
- **vendor_updater_bot**: Read/Write access for relationship creation
- **TeraskyRag**: Read-only access for graph queries

### Communication Pattern
```
[Email Sources] → [vendor_updater_bot] → [Shared Databases] → [TeraskyRag] → [External APIs/UI]
```

### Configuration Management
- Shared database connection parameters
- Environment-specific configuration overrides
- Separate application-specific settings

## Migration Implementation Plan

### Phase 1: Repository Setup (Week 1)
- [x] Create `vendor_updater_bot` repository
- [x] Create `TeraskyRag` repository  
- [x] Set up basic folder structures
- [ ] Initialize Git repositories with proper .gitignore files

### Phase 2: Core Module Migration (Week 2)
- [x] Move ingestion modules to `vendor_updater_bot` (13 files)
- [x] Move search/RAG modules to `TeraskyRag` (8 files)
- [x] Move API files to `TeraskyRag/api/` (4 files)
- [x] Move graph files to `TeraskyRag/graph/` (3 files)
- [x] Duplicate shared utilities (`llm_utils.py`, `config_utils.py`)
- [x] Update import statements in all files

### Phase 3: Configuration Split (Week 3)
- [x] Split `config.yaml` into separate configs
- [x] Create separate `.env.example` files  
- [x] Update configuration loading in both systems
- [x] Removed RAG/Neo4j sections from ingestion config
- [x] Added comprehensive RAG settings to TeraskyRag config
- [x] Test configuration management

**Phase 4 Complete**:
- [x] Separate requirements.txt files created (6 ingestion deps, 12 RAG deps)
- [x] Docker configurations split and customized for each system
- [x] Dockerfiles updated with proper dependencies and structure
- [x] Docker Compose files configured with correct ports and volumes
- [x] TeraskyRag Docker build tested successfully
- [x] vendor_updater_bot Docker build tested successfully
- [x] Dependency conflicts resolved by removing incompatible packages

### Phase 4: Dependencies & Docker (Week 4)
- [x] Create separate `requirements.txt` files
- [x] Split Docker configurations
- [x] Update Dockerfiles for each system
- [x] Test containerized deployments

### Phase 5: Testing & Documentation (Week 5)
- [x] Migrate and organize test files
- [x] Create basic functionality tests for each repository
- [x] Create integration test between systems
- [x] Test data consistency between systems
- [x] Create integration testing strategy
- [x] Fix missing functions in both repositories
- [x] Verify ChromaDB connectivity in both systems
- [x] Update documentation for each repository (README.md)
- [x] Make tests resilient to missing AWS credentials
- [x] Copy API specification to TeraskyRag docs
- [ ] Run pre-migration baseline tests
- [ ] Execute post-migration validation tests
- [ ] Run performance regression tests
- [ ] Validate API compatibility
- [ ] Validate end-to-end functionality

### Phase 6: Validation & Cleanup (Week 6)
- [ ] Run full pipeline tests
- [ ] Validate API functionality
- [ ] Performance testing
- [ ] Final cleanup and optimization

## Testing Strategy

### Pre-Migration Baseline Tests
**Purpose**: Establish current functionality baseline before split

#### Ingestion Pipeline Tests
```bash
# Test full pipeline with sample emails
python main.py --local --folder misc/tst_emls --deletelog

# Validate data storage
python Tests/tools/testChromaDB.py
python Tests/tools/simple_query.py

# Test specific components
python Tests/unit/test_normalize.py
python Tests/unit/test_enrich.py
```

#### RAG System Tests
```bash
# Test search functionality
python Tests/tools/test_search_quality.py
python Tests/tools/debug_search.py

# Test APIs
python Tests/tools/test_rag_api.py
curl http://localhost:8000/health
curl http://localhost:8001/vendors

# Test unified search
python Tests/tools/unified_search.py
```

#### Performance Baseline
```bash
# Capture performance metrics
python src/search_benchmark.py --iterations 5
python Tests/tools/test_analytics.py
```

### Post-Migration Validation Tests

#### Phase 1: Individual Repository Tests

**vendor_updater_bot Repository**:
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
python main.py --local --folder misc/tst_emls --reset-db

# Database connectivity
python tests/tools/test_connection_pooling.py

# Email processing validation
python tests/tools/import_all_emails.py
```

**TeraskyRag Repository**:
```bash
# Unit tests
pytest tests/unit/ -v

# Search functionality
python tests/tools/test_search_quality.py
python tests/tools/debug_search.py

# API endpoints
python tests/tools/test_rag_api.py
curl http://localhost:8000/health
curl http://localhost:8000/metadata

# Graph database queries
python tests/tools/simple_query.py
python tests/tools/cypher_query.py
```

#### Phase 2: Cross-System Integration Tests

**Data Flow Validation**:
```bash
# 1. Run ingestion in vendor_updater_bot
cd vendor_updater_bot
python main.py --local --folder misc/tst_emls --reset-db

# 2. Validate data availability in TeraskyRag
cd ../TeraskyRag
python tests/tools/debug_search.py
curl -X POST http://localhost:8000/query -d '{"query":"test"}'
```

**End-to-End Workflow Tests**:
```bash
# Complete workflow test script
#!/bin/bash
set -e

# Step 1: Fresh ingestion
cd vendor_updater_bot
python main.py --local --folder misc/tst_emls --reset-db --emptydatafolders

# Step 2: Validate ingestion results
echo "Validating ingestion..."
python -c "from src.llm_utils import get_chroma_collection; print(f'ChromaDB docs: {get_chroma_collection().count()}')"

# Step 3: Test RAG system
cd ../TeraskyRag
echo "Testing RAG system..."
python tests/tools/test_search_quality.py

# Step 4: API validation
echo "Testing APIs..."
curl -f http://localhost:8000/health || exit 1
curl -f http://localhost:8001/vendors || exit 1

echo "✅ End-to-end test passed"
```

### Automated Test Suite

#### Continuous Integration Tests
```yaml
# .github/workflows/split-validation.yml
name: Repository Split Validation

on: [push, pull_request]

jobs:
  test-ingestion:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run ingestion tests
        run: |
          python -m pytest tests/unit/ -v
          python main.py --local --folder misc/tst_emls --noevaluation
      - name: Validate data storage
        run: python tests/tools/testChromaDB.py

  test-rag:
    runs-on: ubuntu-latest
    needs: test-ingestion
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run RAG tests
        run: |
          python -m pytest tests/unit/ -v
          python tests/tools/test_search_quality.py
      - name: Test APIs
        run: |
          python api/rag_api.py &
          sleep 10
          curl -f http://localhost:8000/health
```

#### Performance Regression Tests
```python
# tests/performance/test_regression.py
import time
import pytest
from src.search_benchmark import run_benchmark

class TestPerformanceRegression:
    def test_search_performance(self):
        """Ensure search performance doesn't degrade after split"""
        baseline_time = 2.0  # seconds
        
        start_time = time.time()
        results = run_benchmark(iterations=3)
        elapsed = time.time() - start_time
        
        assert elapsed < baseline_time, f"Search too slow: {elapsed}s > {baseline_time}s"
        assert len(results) > 0, "No search results returned"
    
    def test_ingestion_performance(self):
        """Ensure ingestion performance doesn't degrade"""
        baseline_time = 30.0  # seconds per email
        
        start_time = time.time()
        # Run ingestion on sample emails
        elapsed = time.time() - start_time
        
        emails_processed = 5  # sample count
        time_per_email = elapsed / emails_processed
        
        assert time_per_email < baseline_time, f"Ingestion too slow: {time_per_email}s > {baseline_time}s"
```

### Data Consistency Validation

#### Database State Verification
```python
# tests/integration/test_data_consistency.py
import pytest
from src.llm_utils import get_chroma_collection
from graph.graph_db import run_graph_query

class TestDataConsistency:
    def test_chromadb_neo4j_consistency(self):
        """Verify data consistency between ChromaDB and Neo4j"""
        # Get ChromaDB document count
        collection = get_chroma_collection()
        chroma_count = collection.count()
        
        # Get Neo4j email count
        neo4j_result = run_graph_query("MATCH (e:Email) RETURN count(e) as count")
        neo4j_count = neo4j_result[0]['count'] if neo4j_result else 0
        
        # ChromaDB stores chunks, Neo4j stores emails
        # Validate reasonable relationship (chunks >= emails)
        assert chroma_count >= neo4j_count, f"Data inconsistency: ChromaDB({chroma_count}) < Neo4j({neo4j_count})"
    
    def test_metadata_consistency(self):
        """Verify metadata consistency across systems"""
        collection = get_chroma_collection()
        sample_data = collection.get(limit=10)
        
        for metadata in sample_data['metadatas']:
            assert 'vendor' in metadata, "Missing vendor metadata"
            assert 'email_id' in metadata, "Missing email_id metadata"
            assert metadata['vendor'] != 'unknown', "Unprocessed vendor metadata"
```

### API Compatibility Tests

#### Backward Compatibility Validation
```python
# tests/api/test_compatibility.py
import requests
import pytest

class TestAPICompatibility:
    BASE_URL = "http://localhost:8000"
    
    def test_query_endpoint_compatibility(self):
        """Ensure /query endpoint maintains compatibility"""
        payload = {
            "query": "hashicorp vault",
            "metadata_filters": {"vendor": "hashicorp"},
            "top_k": 5
        }
        
        response = requests.post(f"{self.BASE_URL}/query", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert isinstance(data["sources"], list)
    
    def test_metadata_endpoint_compatibility(self):
        """Ensure /metadata endpoint maintains compatibility"""
        response = requests.get(f"{self.BASE_URL}/metadata")
        assert response.status_code == 200
        
        data = response.json()
        assert "vendors" in data
        assert "products" in data
        assert "types" in data
        assert isinstance(data["vendors"], list)
```

### Migration Validation Checklist

#### Pre-Migration Validation
- [ ] Capture baseline performance metrics
- [ ] Document current API response formats
- [ ] Export sample data for comparison
- [ ] Record current test pass rates
- [ ] Backup current databases

#### Post-Migration Validation
- [ ] All unit tests pass in both repositories
- [ ] Integration tests validate cross-system communication
- [ ] API responses match baseline formats
- [ ] Performance metrics within acceptable range
- [ ] Data consistency checks pass
- [ ] Docker containers build and run successfully
- [ ] End-to-end workflow completes successfully

#### Rollback Criteria
- [ ] Any critical functionality broken
- [ ] Performance degradation > 50%
- [ ] Data loss or corruption detected
- [ ] API compatibility broken
- [ ] Unable to complete end-to-end workflow

## Success Criteria

### Functional Requirements
- [ ] Email ingestion pipeline runs independently
- [ ] RAG system provides all current search capabilities
- [ ] APIs maintain backward compatibility
- [ ] Data consistency between systems
- [ ] All baseline tests pass in split repositories

### Non-Functional Requirements
- [ ] Independent deployment capability
- [ ] Maintained performance levels (within 10% of baseline)
- [ ] Clear separation of concerns
- [ ] Comprehensive documentation
- [ ] Zero data loss during migration

### Quality Gates
- [ ] All existing tests pass
- [ ] No regression in functionality
- [ ] Docker containers build and run successfully
- [ ] Integration tests validate system communication
- [ ] Performance regression tests pass
- [ ] API compatibility tests pass
- [ ] Data consistency validation passes

## Risk Mitigation

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Import dependency issues | High | Thorough testing of import statements |
| Configuration conflicts | Medium | Separate config validation |
| Database connection issues | High | Shared connection utilities |
| Performance degradation | Medium | Benchmark testing |

### Operational Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Deployment complexity | Medium | Comprehensive Docker setup |
| Team coordination | Low | Clear ownership boundaries |
| Documentation gaps | Medium | Systematic documentation review |

## Benefits Realization

### Immediate Benefits
- Clear separation of ingestion and query responsibilities
- Independent scaling capabilities
- Simplified maintenance and debugging
- Better team ownership boundaries

### Long-term Benefits
- Technology stack flexibility for each system
- Independent release cycles
- Easier onboarding for new team members
- Improved system reliability through isolation

## Conclusion

This repository split will transform the current monolithic system into two focused, maintainable repositories while preserving all existing functionality. The plan ensures minimal disruption during migration while establishing a foundation for future scalability and maintainability.

## Appendix

### Key Contacts
- **Project Lead**: [To be assigned]
- **Technical Lead**: [To be assigned]
- **DevOps Lead**: [To be assigned]

### Timeline
- **Start Date**: [To be determined]
- **Target Completion**: 6 weeks from start
- **Go-Live Date**: [To be determined]

### Resources Required
- Development team: 2-3 developers
- DevOps support: 1 engineer
- Testing resources: 1 QA engineer
- Documentation: Technical writer support