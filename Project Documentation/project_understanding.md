# Project Understanding: kev-new-graph-rag Hybrid RAG System

This document outlines the current understanding of the `kev-new-graph-rag` project, including its objectives, architecture, core technologies, data pipelines, and configuration management. It serves as a reference for ongoing development.

## 1. Project Goal

The primary objective is to develop a sophisticated hybrid Retrieval Augmented Generation (RAG) system. This system answers natural language queries by synthesizing information from two primary sources:
1.  A structured **knowledge graph** (Neo4j AuraDB) that captures entities and their temporal relationships, managed via **Graphiti**.
2.  A **vector store** (ChromaDB) that contains semantic embeddings of text chunks from ingested documents.

The system is designed for complex reasoning, leveraging both the semantic relevance from the vector store and the contextual, relational insights from the knowledge graph.

## 2. Core Technologies & Frameworks

*   **Backend:** FastAPI
*   **Frontend:** Streamlit
*   **Knowledge Graph:** Neo4j AuraDB, managed with Graphiti (`graphiti-core`)
*   **Vector Store:** ChromaDB
*   **LLM & Embeddings:** Google Gemini (via `google-genai` SDK), authenticated with Vertex AI using Application Default Credentials (ADC).
*   **Configuration:** Pydantic-Settings for type-safe configuration management from `.env` files.
*   **Package Management & Runner:** `uv`

## 3. System Architecture

The project is a full-stack application composed of a FastAPI backend, a Streamlit frontend, and connections to external databases (Neo4j, ChromaDB) and Google Cloud services.

### 3.1. Backend (`src/backend`)

The FastAPI application serves as the core logic hub.
*   **Entry Point:** `src/backend/main_api.py`
*   **API Routers:**
    *   `/api/v2/chat`: Handles user queries, orchestrates the "Super Hybrid" search, and returns synthesized answers.
    *   `/api/v2/ingest`: Provides endpoints for ingesting data from various sources (local files, Google Drive, YouTube URLs).
    *   `/api/v2/graph`: Exposes endpoints for interacting with and visualizing the knowledge graph.
*   **Logging:** Uses **Loguru** for detailed, structured, and colorized logging, configured in `main_api.py`.

### 3.2. Frontend (`src/app`)

The Streamlit application provides the user interface.
*   **Main UI:** `src/app/main_ui.py`
*   **Features:**
    *   A chat interface for asking questions.
    *   Visualization of the knowledge graph context.
    *   Display of retrieved text chunks (vector context).
    *   UI controls for ingesting documents from local files, Google Drive, and YouTube.

### 3.3. Modular Ingestion Pipeline (`src/ingestion`)

The ingestion process is managed by a modular pipeline, designed for flexibility and extensibility.
*   **Orchestrator (`IngestionOrchestrator`):** The main controller that assembles and runs ingestion pipelines based on the data source.
*   **Pipeline (`IngestionPipeline`):** A sequence of `IngestionStep` objects.
*   **Steps (`IngestionStep`):** Atomic units of work (e.g., `GetYoutubeTranscript`, `ChunkDocument`, `ExtractGraph`, `IngestToChromaDB`, `IngestToNeo4j`). This design allows for easily adding new data sources or processing steps.

### 3.4. Super Hybrid Query Orchestration (`src/graph_querying`)

The query process combines the strengths of graph and vector search.
*   **Orchestrator (`SuperHybridOrchestrator`):**
    1.  Receives a user query.
    2.  Queries **ChromaDB** for semantically similar text chunks.
    3.  Queries **Neo4j/Graphiti** for relevant graph context.
    4.  Combines both sets of results.
    5.  Sends the combined context to the Gemini LLM for a final, synthesized answer.

## 4. Ontology (`src/ontology_templates/universal_ontology.py`)

The project employs a universal ontology designed for multi-domain knowledge extraction.
*   **Core Entity Types (9):** `Person`, `Organization`, `Location`, `Event`, `Technology`, `Content`, `Topic`, `Resource`, `Agreement`.
*   **Universal Relationship Types (10):** `Participates`, `Located`, `Creates`, `Uses`, `Supports`, `Opposes`, `Discusses`, `Controls`, `Collaborates`, `Influences`.
*   All models are based on `pydantic.BaseModel`.

## 5. Configuration Management (`src/utils/config_models.py`)

Configuration is managed centrally and loaded automatically at runtime.
*   **Mechanism:** Uses `pydantic-settings.BaseSettings`.
*   **Source:** All configuration is loaded from the `.env` file at the project root.
*   **Models:** Typed Pydantic models (`Settings`, `Neo4jConfig`, `ChromaDBConfig`, etc.) provide configuration to the application, ensuring all required settings are present and correctly typed at startup. Manual parsing of `.env` or YAML files has been deprecated.

## 6. Custom Gemini Embedding (`src/utils/embedding.py`)

The project uses a custom `CustomGeminiEmbedding` class for generating embeddings.
*   **Rationale:** This custom class provides better integration with the project's architecture than the default `GeminiEmbedder` from Graphiti.
*   **Key Features:**
    *   **Vertex AI ADC Integration:** Natively supports authentication via Application Default Credentials.
    *   **LlamaIndex Compatibility:** Inherits from `llama_index.core.embeddings.BaseEmbedding`.
    *   **Optimized Parameters:** Passes `task_type` and `title` to the Gemini API for higher-quality embeddings.
