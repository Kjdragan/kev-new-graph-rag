# Project Development Log & Lessons Learned

This document tracks the major development milestones, architectural decisions, and key lessons learned during the construction of the hybrid RAG system.

## Key Development Milestones

### 1. Migration to Modular, UI-Driven Ingestion
**Status:** Complete

**Summary:** The original, script-based ingestion process (`scripts/ingest_gdrive_documents.py`) was completely replaced with a flexible, modular pipeline architecture.
*   **Components:** `IngestionOrchestrator`, `IngestionPipeline`, and a series of `IngestionStep` classes were created in `src/ingestion`.
*   **Features:** The new system supports ingestion from local file uploads, Google Drive folders, and YouTube URLs.
*   **Interface:** Ingestion is now triggered exclusively through the Streamlit UI, which calls dedicated FastAPI endpoints in `src/backend/routers/ingest.py`.
*   **Lesson Learned:** A modular pipeline is far more maintainable and extensible than monolithic scripts, making it easy to add new data sources and processing steps.

### 2. Implementation of "Super Hybrid" Query Orchestration
**Status:** Complete

**Summary:** The query engine was upgraded from a simple graph search to a "Super Hybrid" model that leverages both the knowledge graph and the vector store.
*   **Component:** The `SuperHybridOrchestrator` was created in `src/graph_querying/super_hybrid_orchestrator.py`.
*   **Process:** For each query, it retrieves context from both ChromaDB (vector search) and Neo4j/Graphiti (graph search), then synthesizes the combined results using an LLM to generate a comprehensive answer.
*   **Interface:** The main `/chat` endpoint now uses this orchestrator, and the Streamlit UI has been updated to display both graph and vector context.
*   **Lesson Learned:** Combining retrieval methods provides more robust and contextually rich answers than either method alone.

### 3. Refactoring Configuration with Pydantic-Settings
**Status:** Complete

**Summary:** All configuration management was centralized and refactoreed to use the `pydantic-settings` library.
*   **Component:** All configuration models are now defined in `src/utils/config_models.py` and inherit from `BaseSettings`.
*   **Process:** Configuration is loaded automatically from the `.env` file at startup. This provides type safety and eliminates the need for manual `dotenv` or `yaml` parsing.
*   **Lesson Learned:** Using a dedicated configuration library like `pydantic-settings` simplifies code, reduces boilerplate, and prevents runtime errors due to missing or malformed configuration.

### 4. Enhanced Logging and Error Reporting
**Status:** Complete

**Summary:** The backend application's observability was significantly improved.
*   **Logging:** Loguru was integrated into `src/backend/main_api.py` to provide detailed, structured, and colorized console logs.
*   **Error Reporting:** The FastAPI endpoints were refactored to return structured JSON error messages instead of poorly formatted strings, making API-level debugging much easier.
*   **Lesson Learned:** Investing in proper logging and error handling early is critical for efficient debugging, especially in a complex, multi-component system.

### 5. YouTube Transcript Ingestion
**Status:** In Progress

**Summary:** The modular ingestion pipeline was extended to support fetching and processing YouTube transcripts.
*   **Components:** A `GetYoutubeTranscript` step was added to `src/ingestion/steps.py`, and a corresponding endpoint was added to the `ingest` router.
*   **Current State:** The feature is implemented but currently undergoing debugging to resolve runtime errors in the ingestion pipeline.

### 6. Gemini Embedding Client Initialization
**Status:** Complete

**Summary:** A series of critical errors preventing the successful generation of embeddings via Vertex AI were identified and resolved. This was a multi-step debugging process.
*   **Problem 1: `TypeError` on Client Initialization:** The `genai.Client` was being initialized with an unsupported `client_options` dictionary, causing a `TypeError`.
    *   **Fix:** The initialization was corrected to use the documented keyword arguments: `genai.Client(vertexai=True, project=project_id, location=location)`. This lesson was documented in `workingwithgenai.md`.
*   **Problem 2: `AttributeError` on Project ID Retrieval:** After fixing the `TypeError`, a subsequent `AttributeError: 'IngestionOrchestratorConfig' object has no attribute 'google'` occurred.
    *   **Fix:** The code was incorrectly trying to access the GCP Project ID from the Pydantic configuration object. The fix was to retrieve the project ID directly from the `GOOGLE_CLOUD_PROJECT` environment variable, which is the standard practice when using Application Default Credentials (ADC) with the `google-genai` SDK.
*   **Current State:** The `CustomGeminiEmbedding` class in `utils/embedding.py` now correctly initializes the Vertex AI client. The ingestion pipeline is ready for a full validation run.
