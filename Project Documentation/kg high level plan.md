# Master Build Plan: Advanced RAG + Knowledge Graph System

This document outlines a comprehensive, step-by-step approach to building the hybrid RAG + Knowledge Graph system according to the PRD requirements. Each main task is broken down into specific subtasks with implementation details.

## 1. Project Setup and Environment Configuration

1. **Create project structure**
   - Set up directories for modules, tests, and configuration
   - Initialize Git repository if not already done
   - Create `.gitignore` for Python projects
   - Set up `parsed_documents` directory for document storage

2. **Configure Python environment**
   - Verify Python 3.12 environment (already initialized with uv)
   - Set up `pyproject.toml` with required dependencies
   - Create version-agnostic `requirements.txt` for reference

3. **Install core dependencies**
   - Install LlamaIndex with `uv add llama-index`
   - Install pgvector with `uv add pgvector`
   - Install Neo4j client with `uv add neo4j`
   - Install Google AI libraries with `uv add google-ai-generativelanguage google-cloud-aiplatform`
   - Install Supabase client with `uv add supabase`

4. **Set up environment variables**
   - Create `.env` template
   - Add configuration for Supabase credentials
   - Add configuration for Neo4j credentials
   - Add configuration for Google Vertex AI credentials

5. **Create build progress tracking**
   - Initialize `build_progress.md` file
   - Create sections for tracking ingestion, vector indexing, and KG extraction
   - Set up formatting for timestamp logging
   - Create `failed_upserts.log` for recording failures

## 2. Database Infrastructure Setup

1. **Set up Supabase vector store**
   - Initialize Supabase connection
   - Create `docs_index` table with the specified schema
   - Enable pgvector extension and create indices
   - Test connection and basic vector operations
   - Document Supabase setup in `build_progress.md`

2. **Configure Neo4j database**
   - Set up Neo4j AuraDB connection
   - Create Neo4j schema constraints for entities and relationships
   - Implement MERGE operations for upsert functionality
   - Test connection with sample Cypher queries
   - Document Neo4j setup in `build_progress.md`

3. **Create database helper functions**
   - Implement connection pooling for Supabase
   - Implement connection pooling for Neo4j
   - Create retry mechanisms with tenacity for database operations
   - Create helper functions for data validation
   - Document helper functions in code comments

4. **Implement logging mechanisms**
   - Set up Python logging
   - Configure log rotation
   - Create functions to update `build_progress.md`
   - Implement error logging for failed database operations
   - Create visualization helpers for build progress

5. **Create database cleanup utilities**
   - Implement vector index reset functionality
   - Implement KG index reset functionality
   - Create database health check utilities
   - Document database management operations
   - Implement backup functionality for indices

## 3. Document Ingestion and Indexing

1. **Integrate existing gdrive_llamaparse_ingester**
   - Copy module into project structure
   - Review and understand module functionality
   - Update imports and dependencies as needed
   - Test module with sample documents
   - Document integration in `build_progress.md`

2. **Implement document loading functionality**
   - Create `load_parsed_documents` function
   - Scan parsed_dir for JSON files
   - Parse JSON into LlamaIndex Documents
   - Add source tracking metadata
   - Implement tracking of processed documents

3. **Set up vector indexing**
   - Initialize GoogleGenAIEmbedding with `gemini-embedding-001`
   - Configure embedding dimension reduction to 1800
   - Implement SupabaseVectorStore connection
   - Create vector indexing pipeline
   - Test embeddings with sample documents

4. **Implement Knowledge Graph extraction**
   - Initialize Neo4jGraphStore
   - Configure Knowledge Graph extraction settings
   - Create triple extraction pipeline using Gemini 2.5 Pro
   - Implement entity typing in extraction
   - Test KG extraction with sample documents

5. **Create ingestion orchestration**
   - Implement `run` function to coordinate ingestion
   - Create batch processing functionality
   - Implement progress tracking during ingestion
   - Add validation checks for indexed documents
   - Create command-line interface for ingestion

## 4. Query Engine Development

1. **Implement VectorQueryEngine**
   - Create `VectorQueryEngine` class
   - Implement similarity search functionality
   - Configure retrieval parameters (top-k, etc.)
   - Add metadata filtering options
   - Test with sample queries

2. **Implement KnowledgeGraphQueryEngine**
   - Create `KnowledgeGraphQueryEngine` class
   - Implement entity-based and relationship-based queries
   - Configure Cypher query generation from natural language
   - Add result formatting functionality
   - Test with sample queries

3. **Create ReRanker functionality**
   - Implement `ReRanker` class using Gemini 2.5 Flash
   - Create relevance scoring logic
   - Implement cross-comparison between results
   - Configure model parameters for optimal performance
   - Test re-ranking with sample query results

4. **Develop HybridQueryEngine**
   - Create `HybridQueryEngine` class as specified
   - Implement router logic using heuristics
   - Create response synthesis using Gemini 2.5 Pro
   - Configure metadata formatting for responses
   - Implement citation generation

5. **Add query engine utilities**
   - Create query preprocessing functions
   - Implement response formatting utilities
   - Create timing and performance tracking
   - Add debugging functionality
   - Implement query logging

## 5. Testing and Validation

1. **Create unit tests**
   - Set up pytest framework
   - Create tests for document loading
   - Create tests for vector indexing
   - Create tests for KG extraction
   - Implement tests for query engines

2. **Implement end-to-end testing**
   - Create sample dataset for testing
   - Design test cases covering full pipeline
   - Implement performance benchmarks
   - Create test documentation
   - Add CI workflow for automated testing

3. **Create validation utilities**
   - Implement embedding validation
   - Create KG validation functions
   - Implement query result validation
   - Create database validation utilities
   - Document validation methodology

4. **Performance testing**
   - Create benchmarking script for ingestion
   - Measure query latency across different approaches
   - Test system with increasing document volumes
   - Profile memory usage
   - Document performance results

5. **Error handling and resilience**
   - Test retry mechanisms
   - Verify error logging
   - Implement circuit breakers for external services
   - Test recovery from failure scenarios
   - Document error handling strategy

## 6. User Interface and Tools

1. **Create CLI interface**
   - Implement command-line arguments parsing
   - Create commands for ingestion, indexing, and querying
   - Add configuration options via CLI
   - Implement progress display
   - Create help documentation

2. **Implement interactive query tool**
   - Create simple terminal-based query interface
   - Implement query history
   - Add result formatting options
   - Create debugging mode
   - Implement example queries

3. **Develop visualization utilities**
   - Create knowledge graph visualization helpers
   - Implement query result visualization
   - Create build progress visualization
   - Add performance metrics visualization
   - Document visualization options

4. **Add administrative tools**
   - Create database management utilities
   - Implement index management commands
   - Add system status reporting
   - Create maintenance scripts
   - Document administrative procedures

5. **Create documentation**
   - Write detailed API documentation
   - Create usage examples
   - Document system architecture
   - Create troubleshooting guide
   - Compile performance optimization tips

## 7. Optimization and Enhancement

1. **Optimize vector search**
   - Tune pgvector parameters for optimal performance
   - Implement filtered vector search
   - Optimize embedding pipeline
   - Analyze and reduce latency
   - Document optimization results

2. **Enhance knowledge graph**
   - Add entity typing as specified
   - Implement community detection
   - Add cluster summarization
   - Optimize triple extraction quality
   - Improve relationship typing

3. **Optimize query performance**
   - Implement query caching
   - Optimize routing heuristics
   - Tune re-ranking parameters
   - Implement parallel processing
   - Measure and document performance improvements

4. **Add system monitoring**
   - Implement telemetry
   - Create performance dashboards
   - Add alerting for failures
   - Implement usage tracking
   - Document monitoring setup

5. **Future enhancements**
   - Research multi-modal extensions
   - Explore conversation memory
   - Investigate streaming responses
   - Consider specialized embeddings for specific domains
   - Document roadmap for future development
