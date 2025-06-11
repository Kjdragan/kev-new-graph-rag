# Kev-Graph-RAG: Unified Google Drive Ingestion Build Plan (ChromaDB & Neo4j)

**Version:** 2.0
**Date:** 2025-06-09

## 1. Overview & Strategy

This document outlines the build plan for integrating Google Drive document ingestion, LlamaParse parsing, and subsequent indexing into **both ChromaDB (for traditional vector RAG) and Neo4j (for graph-enhanced RAG)** within the `kev-graph-rag` project.

The strategy is as follows:
1.  **Implement ChromaDB Path for Vector Storage:** Set up a Docker-based ChromaDB instance for efficient vector storage and retrieval. ChromaDB will store document text, embeddings, and metadata in a single system.
2.  **Implement Neo4j Path for Graph-Enhanced RAG:** Process the parsed documents for ingestion into Neo4j as `:Document` nodes with associated embeddings.
3.  **Standardized Embeddings:** Both ChromaDB and Neo4j ingestion paths will use the **`gemini-embedding-exp-03-07` model (1024 dimensions)** via the `CustomGeminiEmbedding` utility for consistency.

This will result in a single ingestion pipeline capable of feeding two distinct RAG backends from the same source documents.

## 2. Core Utility Development (Common Components)

This phase focuses on creating the foundational Python modules in `kev-graph-rag/utils/`.

*   **Task 2.1: Configuration Models (`utils/config_models.py`)**
    *   [x] Define `GDriveReaderConfig` for Google Drive settings.
    *   [x] Define `LlamaParseConfig` for LlamaParse API settings.
    *   [x] Define `ChromaDBConfig` for ChromaDB connection (host, port, collection name, auth).
    *   [x] Define `Neo4jConfig` for Neo4j connection (URI, user, password).
    *   [x] Define `EmbeddingConfig` (or integrate into orchestrator config) specifying model name (`gemini-embedding-exp-03-07`) and dimension (1024).
*   **Task 2.2: Google Drive Reader (`utils/gdrive_reader.py`)**
    *   [x] Implement `GDriveReader` class for authenticating and fetching files/content from Google Drive.
    *   [x] Methods: `list_files`, `download_file_to_path`, `read_file_content`.
*   **Task 2.3: Document Parser (`utils/document_parser.py`)**
    *   [x] Implement `DocumentParser` class using `llama-cloud-services`.
    *   [x] Method `parse_file` to process a local file and return structured parsed data (e.g., list of page/section dictionaries similar to `kev_adv_rag`'s LlamaParse output, or directly as LlamaIndex `Document` objects).
    *   [x] Method `parse_file_to_concatenated_text` for Neo4j path.
*   **Task 2.4: Custom Embedding Utility (`utils/embedding.py`)**
    *   [x] Ensure `CustomGeminiEmbedding` class correctly uses `gemini-embedding-exp-03-07` and handles 1024 dimensions.
    *   [x] Verify compatibility with LlamaIndex `BaseEmbedding` interface.
*   **Task 2.5: Dependency Management**
    *   [x] Add `google-auth`, `google-api-python-client`, `llama-cloud-services`, `pydantic`, `loguru`, `tenacity`.
    *   [x] Add/Verify `neo4j` (driver), `google-genai`.
    *   [ ] Remove `supabase`, `llama-index-vector-stores-supabase` dependencies.
    *   [ ] Add `chromadb` dependency.
    *   [ ] Run `uv sync` after updates.

## 3. ChromaDB Docker Setup and Integration

This phase focuses on setting up and integrating ChromaDB for vector storage.

*   **Task 3.1: Docker Setup for ChromaDB**
    *   [x] Create `docker-compose.yml` with ChromaDB configuration.
    *   [ ] Add documentation for starting the ChromaDB Docker container.
    *   [ ] Add environment variables for ChromaDB configuration to `.env.template`.
*   **Task 3.2: ChromaDB Ingester Utility (`utils/chroma_ingester.py`)**
    *   [x] Create `ChromaIngester` class.
    *   [x] Implement methods to initialize ChromaDB client and collection.
    *   [x] Implement `batch_embed_documents` method for efficient embedding generation.
    *   [x] Implement `ingest_documents` method:
        *   Accept a list of documents with text, metadata, and IDs.
        *   Generate embeddings using `CustomGeminiEmbedding` (1024 dims).
        *   Store documents, embeddings, and metadata in ChromaDB.
    *   [x] Implement `search` method for vector similarity search.

## 4. Neo4j Ingestion Path Development

This phase focuses on storing processed documents and their embeddings into Neo4j.

*   **Task 4.1: Neo4j Ingester Utility (`utils/neo4j_ingester.py`)**
    *   [x] Implement `Neo4jIngester` class.
    *   [x] Define `DocumentIngestionData` Pydantic model for Neo4j data structure.
    *   [x] Method to initialize Neo4j driver (using `Neo4jConfig`).
    *   [x] Method `ingest_document` to merge `:Document` nodes with properties (doc_id, filename, content, 1024-dim embedding, metadata).
    *   [x] Method `ensure_constraints_and_indices` to create unique constraint on `doc_id` and a vector index on `embedding` (1024 dimensions, cosine similarity).

## 5. Orchestration Script (`scripts/ingest_gdrive_documents.py`)

This script will manage the end-to-end ingestion pipeline for both ChromaDB and Neo4j.

*   **Task 5.1: Setup and Configuration**
    *   [ ] Implement argument parsing (e.g., for GDrive `folder_id`, `.env` path).
    *   [ ] Load configurations from `.env` and CLI arguments for GDrive, LlamaParse, ChromaDB, Neo4j, and Embeddings.
    *   [ ] Initialize: `GDriveReader`, `DocumentParser`, `CustomGeminiEmbedding`, `ChromaIngester`, `Neo4jIngester`.
*   **Task 5.2: Initial Neo4j Setup**
    *   [ ] Call `neo4j_ingester.ensure_constraints_and_indices()`.
*   **Task 5.3: Main Processing Loop**
    *   [ ] Fetch list of files from Google Drive using `GDriveReader`.
    *   [ ] For each file:
        *   Download/read file content.
        *   Create a temporary local path for the file if LlamaParse requires it.
        *   Parse the file using `document_parser.parse_file()` to get structured page data or LlamaIndex `Document` objects.
        *   Log progress and any errors.
        *   **ChromaDB Ingestion Sub-Path:**
            *   Convert parsed data to document dictionaries with unique IDs, text content, and metadata.
            *   Call `chroma_ingester.ingest_documents()` with these documents.
        *   **Neo4j Ingestion Sub-Path:**
            *   Concatenate all text from the parsed sections/pages of the current GDrive file using `document_parser.parse_file_to_concatenated_text()`.
            *   Generate a single embedding for this concatenated text using `custom_gemini_embedding._get_text_embedding()` (1024 dims).
            *   Prepare `DocumentIngestionData` (using GDrive file ID as `doc_id`, filename, concatenated text, generated embedding, and other metadata from GDrive/parsing).
            *   Call `neo4j_ingester.ingest_document()`.
        *   Clean up temporary downloaded files.
*   **Task 5.4: Logging and Error Handling**
    *   [ ] Implement robust logging throughout the script.
    *   [ ] Implement error handling and retry mechanisms where appropriate.

## 6. Testing and Validation

*   **Task 6.1: Unit Tests**
    *   [ ] Write unit tests for `GDriveReader`, `DocumentParser`, `ChromaIngester`, `Neo4jIngester`.
*   **Task 6.2: Integration Tests**
    *   [ ] Test the GDrive -> LlamaParse -> ChromaDB path.
    *   [ ] Test the GDrive -> LlamaParse -> Neo4j path.
*   **Task 6.3: End-to-End Testing**
    *   [ ] Run the full `ingest_gdrive_documents.py` script with sample GDrive documents.
    *   [ ] Verify data integrity in ChromaDB (check text, embeddings, metadata, vector search works).
    *   [ ] Verify data integrity in Neo4j (check `:Document` nodes, properties, vector index, vector search works via `hybrid_search_demo.py`).

## 7. Future Considerations (Post-MVP)

*   Incremental ingestion (processing only new/updated GDrive files).
*   More sophisticated document chunking strategies for Neo4j if individual page-level nodes are desired later.
*   Error queues and dead-letter handling for failed documents.
*   Performance optimization for large-scale ingestion.
*   Hybrid search capabilities combining ChromaDB vector search with metadata filtering.
*   Integration with LlamaIndex for advanced retrieval techniques.
