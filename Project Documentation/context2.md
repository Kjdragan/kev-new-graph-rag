# Project Development Log & Lessons Learned

## Summary of Recent Work (UI-Driven Ingestion)

This document tracks the progress of implementing a UI-driven document ingestion pipeline.

### Key Features Implemented

1.  **Backend Ingestion Endpoint:**
    - A new POST endpoint was created at `/api/v2/ingest/document` in `src/backend/routers/ingest.py`.
    - This endpoint accepts a file upload (`UploadFile`).
    - It reads the file content, decodes it, and passes it to the `GraphExtractor`.

2.  **Core Ingestion Logic:**
    - The endpoint initializes the `GraphExtractor` from `src/graph_extraction/extractor.py`.
    - It calls the `extractor.extract()` method, providing the document's text content.
    - The `universal_ontology.py` (`NODE_TYPES`, `RELATIONSHIP_TYPES`) is used to provide the schema for knowledge extraction.

3.  **API Integration:**
    - The new `ingest` router was registered with the main FastAPI application in `src/backend/main_api.py` to make the endpoint accessible.

4.  **Frontend UI (Completed):**
    - A file uploader component was added to the Streamlit interface in `src/app/main_ui.py`.
    - It is placed in an `st.expander` to keep the UI clean.
    - The UI calls the new backend endpoint to trigger the ingestion process and displays the status to the user.

---

## Onboarding Instructions

To get up to speed on this project, review the following files and directories. They provide essential context on the project's goals, architecture, configuration, and current implementation.

### Core Project & Framework Documentation
- **Frameworks:**
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\Project Documentation\workingwithgenai.md]` - Explains how to use the `google-genai` SDK with ADC.
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\Project Documentation\understanding_graphiti_search.md]` - Details the principles of Graphiti-native search.
- **Overall Project:**
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\Project Documentation\project_understanding.md]` - High-level overview of the project goals and architecture.

### Project-Specific Implementation & Configuration
- **Configuration:**
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\.env]` - Environment variables for Neo4j, Google Cloud, etc.
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\config.yaml]` - Application-level configuration, including model IDs.
- **Backend Code:**
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\src\backend]` - The main FastAPI application, including all routers (chat, graph, ingest).
- **Querying & Ingestion:**
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\src\graph_querying\test_hybrid_search.py]` - Example usage of the `GraphitiNativeSearcher`.
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\scripts\ingest_gdrive_documents.py]` - The original manual ingestion script (Note: this is being replaced by the UI-driven workflow).

*This list is dynamic and should be updated as the project evolves and manual scripts are replaced by modular, UI-driven components.*

This document tracks the development progress, key architectural decisions, and lessons learned during the construction of the hybrid RAG system.

## Key Development Milestones

### 1. Refactoring Graph Visualization to be Graphiti-Native

**Initial State:** The graph visualization was initially implemented using a direct, raw Cypher query to fetch all nodes and relationships from Neo4j. 

**Problem:** The user correctly pointed out that this approach bypassed the `Graphiti` abstraction layer, which is a core component of the project's architecture. All database interactions are intended to flow through Graphiti to leverage its features like search recipes, reranking, and native query generation.

**Solution:**
- The backend endpoint `/api/v2/graph/full_graph` in `src/backend/routers/graph.py` was refactored.
- It now uses the `GraphitiNativeSearcher` class from `src/graph_querying/graphiti_native_search.py`.
- Specifically, it calls the `advanced_search_with_recipe` method with a generic query (`*`) to fetch a representative sample of the graph.
- The endpoint was converted to `async` to support the asynchronous nature of the `GraphitiNativeSearcher`.

**Lesson Learned:** Adherence to the established architecture is critical. Using Graphiti-native functions instead of raw Cypher is essential for maintainability, scalability, and leveraging the full power of the framework.

### 2. Implementing UI-Driven Document Ingestion

**Goal:** Enable users to upload documents directly through the Streamlit UI for ingestion into the knowledge graph.

**Implementation Steps:**

1.  **Backend Endpoint:**
    - A new endpoint `POST /api/v2/ingest/document` was created in `src/backend/routers/ingest.py`.
    - This endpoint accepts a file upload (`UploadFile`).
    - It reads the file content, decodes it, and passes it to the `GraphExtractor`.

2.  **Core Ingestion Logic:**
    - The endpoint initializes the `GraphExtractor` from `src/graph_extraction/extractor.py`.
    - It calls the `extractor.extract()` method, providing the document's text content.
    - The `universal_ontology.py` (`NODE_TYPES`, `RELATIONSHIP_TYPES`) is used to provide the schema for knowledge extraction.

3.  **API Integration:**
    - The new `ingest` router was registered with the main FastAPI application in `src/backend/main_api.py` to make the endpoint accessible.

4.  **Frontend UI (In Progress):**
    - Work has begun on adding a file uploader component to the Streamlit interface in `src/app/main_ui.py`.
    - This will be placed in an `st.expander` to keep the UI clean.
    - The UI will call the new backend endpoint to trigger the ingestion process and display the status to the user.

**Next Steps:** Complete the frontend implementation for the file uploader and test the end-to-end ingestion flow.
