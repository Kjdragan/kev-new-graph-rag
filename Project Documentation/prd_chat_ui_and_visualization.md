# PRD: Interactive Chat UI, Graph Visualization & Enhanced Ingestion

**Version:** 1.1
**Date:** 2025-06-16

## 1. Introduction & Goal

The `kev-new-graph-rag` project has successfully established a robust backend for hybrid search using `GraphitiNativeSearcher`, combining semantic and knowledge graph retrieval. This phase aims to build a user-facing Streamlit application that makes this backend accessible and intuitive, introduces interactive graph visualizations, and enhances the data ingestion process.

We will create a web-based chat interface for natural language queries and answers, visualize the underlying knowledge graph, and provide a UI-driven method for ingesting new documents from Google Drive.

## 2. Core Objectives

- **Implement a Web-Based Chat Interface (Streamlit):** Create a user-friendly interface for submitting queries and viewing conversational responses, leveraging Streamlit's capabilities.
- **Integrate Interactive Graph Visualizations:** Display the graph-based context (nodes and edges from `GraphitiNativeSearcher` results) directly within Streamlit, allowing users to visually explore connections.
- **Implement LLM-Powered Answer Synthesis:** Use a Gemini model (via `google-genai` SDK) to synthesize search results from the `GraphitiNativeSearcher` (e.g., `hybrid_search` output) into coherent, natural language answers.
- **Display Source Attribution:** Provide clear links/references in the UI to the source documents or specific graph elements (nodes/edges with their properties) that form the basis of a generated answer.
- **Manage Basic Conversation History:** Enable multi-turn, contextual conversations by passing recent conversational turns to the backend to inform follow-up queries. Advanced, persistent, graph-based memory (e.g., using Zep with Graphiti) is a future consideration.
- **Develop an Interactive Ingestion Module:** Integrate a UI component in Streamlit to allow users to select and trigger the ingestion of documents from Google Drive and YouTube video transcripts.
- **Refactor Ingestion Pipeline for Modularity:** Re-architect the ingestion process (currently in `scripts/ingest_gdrive_documents.py`) into a modular pipeline where steps like document parsing (e.g., LlamaParse) can be selectively applied or skipped based on the source type.

## 3. Functional Requirements

### 3.1. Chat Component (Streamlit)
- **Query Input**: A Streamlit text input (`st.text_input`) for users to type and submit questions.
- **Conversation Display**: A Streamlit container (`st.container`) or similar to display the history of user queries and system responses in a chat-like format.
- **Streaming Responses**: Answers from the backend (FastAPI endpoint) should stream token-by-token to the Streamlit UI for improved perceived performance.
- **Copy Response**: A button (`st.button`) associated with each system response to copy its text content to the clipboard.
- **Conversation Context**: The Streamlit app will maintain a session-based list of recent (e.g., last 3-5) query-response pairs. This context will be passed to the backend with each new query to allow the `GraphitiNativeSearcher` or the answer synthesis LLM to consider it.

### 3.2. Graph Visualization Component (Streamlit)
- **Data Source**: The component will visualize graph data (nodes and edges) returned by the `GraphitiNativeSearcher` methods (e.g., `hybrid_search`, `entity_focused_search`). This data includes node properties (name, summary, type, UUID) and edge properties (fact, type, UUID, temporal attributes).
- **Dynamic Rendering**: When an answer is generated, a corresponding graph visualization will be rendered in a dedicated section of the Streamlit UI (e.g., using `st.expander` or a tab).
- **Recommended Libraries**: 
    - **Primary**: `streamlit-agraph` for its direct Streamlit integration and use of `vis.js`.
    - **Alternative**: `pyvis` (generating an HTML file to be embedded via `st.components.v1.html`).
- **Interactivity**: 
    - Pan and zoom.
    - Clicking on a node to display its key properties (name, summary, type, original `group_id` from ingestion) in a sidebar or tooltip within Streamlit.
    - Hover-over effects for nodes/edges if supported by the chosen library.
- **Customization**: Ability to configure basic visual aspects (node colors by type, edge labels) if feasible with the chosen library.

### 3.3. Answer Synthesis & Sourcing (Backend via FastAPI, Displayed in Streamlit)
- **Backend Synthesis Module**: 
    - A Python module/class that takes the **fused and re-ranked evidence** from the "Super Hybrid Query Orchestration" stage (Section 3.6).
    - This module will use the `google-genai` SDK (configured as per `workingwithgenai.md` and `.env` settings like `GOOGLE_GENAI_USE_VERTEXAI`) with a Gemini model (e.g., `gemini-pro` from `config.yaml`).
    - It will craft a prompt that includes the user's query, conversational context, and the diverse evidence (text snippets from ChromaDB chunks, key facts/nodes/edges from Neo4j/Graphiti) to generate a concise, natural language answer.
- **UI Display**: The synthesized answer will be the primary response shown in the Streamlit chat interface.
- **Source Links/Attribution**: 
    - Below the synthesized answer, an expandable section (`st.expander`) titled "Sources" or similar.
    - This section must clearly distinguish and list key source elements: 
        *   **From ChromaDB**: e.g., document chunk identifiers, snippets of text, original document name/ID.
        *   **From Neo4j/Graphiti**: e.g., node names (`node['name']`), summaries (`node['summary']`), edge facts (`edge['fact']`), and their respective UUIDs or types.

### 3.4. Interactive Ingestion Module (Streamlit UI & FastAPI Backend)
- **UI Component (Streamlit)**:
    - A dedicated page or section in the Streamlit app for "Data Ingestion".
    - **Google Drive Ingestion Sub-section:**
        - Input field for users to specify a Google Drive Folder ID (overriding the default from `.env`'s `GOOGLE_DRIVE_FOLDER_ID` if needed).
        - A button to "List Files from GDrive". This will call a backend API endpoint.
        - A display area (e.g., `st.multiselect` or a table with checkboxes) showing files from the specified GDrive folder, allowing users to select specific files for ingestion.
        - An "Ingest Selected GDrive Files" button.
    - **YouTube Transcript Ingestion Sub-section:**
        - Input field (`st.text_input`) for users to paste a YouTube video URL.
        - An "Ingest YouTube Transcript" button.
- **Backend API Endpoints (FastAPI)**:
    - `/list_gdrive_files`: Takes a `folder_id` (and uses `GDriveReaderConfig` from `ingest_gdrive_documents.py`'s setup logic) to call `GDriveReader.list_files()` and return the file list.
    - `/ingest_gdrive_documents`: Takes a list of GDrive file IDs and a target `group_id`.
        - This endpoint will utilize the **refactored, modular ingestion pipeline**.
        - **Fetcher**: `GDriveReader.download_file_to_path()`.
        - **Parser**: `DocumentParser.aparse_file()` (as GDrive files might be PDFs, etc.).
        - **Remaining steps**: Chunking (if needed), `CustomGeminiEmbedding`, `GraphExtractor.extract()` (with `universal_ontology.py`), `ChromaIngester`, Neo4j storage.
        - Provide feedback to the Streamlit UI about ingestion progress.
    - `/ingest_youtube_transcript`: Takes a `youtube_url` and a target `group_id`.
        - This endpoint will orchestrate the refactored ingestion pipeline specific to YouTube transcripts, as detailed in Section 3.5. The FastAPI backend itself makes the call to the `mcp2_get_transcript` tool as part of the `YouTubeTranscriptFetcher` logic.
        - Provide feedback to the Streamlit UI.

### 3.5. Refactored Ingestion Pipeline (Backend Logic)

### 3.6. Super Hybrid Query Orchestration (Backend Logic)
- **Goal**: To leverage the distinct strengths of ChromaDB (for broad semantic search over document chunks) and Neo4j/Graphiti (for structured knowledge graph search, entity focus, and graph pattern matching) to produce richer, more accurate answers.
- **Orchestration Flow (within FastAPI `/chat` endpoint logic):**
    1.  **Query Input**: User's natural language query and conversational context (from Streamlit UI).
    2.  **Query Embedding**: Generate a query embedding using `CustomGeminiEmbedding._get_text_embedding()` for semantic search components.
    3.  **Parallel Retrieval**: Execute two retrieval paths concurrently:
        *   **Path A: ChromaDB Semantic Search (Vector Store)**:
            *   Use the query embedding to search ChromaDB.
            *   Retrieve top N semantically similar document chunks (text content + metadata).
        *   **Path B: Neo4j/Graphiti Hybrid Search (Knowledge Graph)**:
            *   Utilize `GraphitiNativeSearcher` methods (e.g., `hybrid_search`, `entity_focused_search`, or `advanced_search_with_recipe` as appropriate, possibly chosen by a simple routing mechanism based on query type if deemed necessary later).
            *   Input the user's query text and/or the pre-computed query embedding (via `query_vector` parameter).
            *   Retrieve relevant graph elements (nodes, edges, paths), entity summaries, and text snippets from node properties.
    4.  **Evidence Fusion & Re-ranking**: 
        *   Collect all retrieved items (document chunks from ChromaDB, graph elements/snippets from Neo4j/Graphiti).
        *   Implement a re-ranking strategy to score and sort the combined evidence. Options include:
            *   **Reciprocal Rank Fusion (RRF):** If both paths provide ranked lists.
            *   **LLM-based Re-ranker:** A separate Gemini model call to evaluate the relevance of each piece of combined evidence against the original query.
            *   **Heuristic/Rule-based:** Combine scores based on source, type of match, etc. (Initial approach might be simpler, with LLM re-ranking as an enhancement).
    5.  **Contextualization for Answer Synthesis**: The top K re-ranked pieces of fused evidence (a mix of text chunks and graph context) will form the input for the LLM-powered answer synthesis stage.


- The core ingestion logic, currently in `scripts/ingest_gdrive_documents.py`, will be refactored into a series of reusable components/classes within the `src` directory (e.g., under `src.ingestion`).
- The goal is to produce a list of processed "document chunks" (e.g., LlamaIndex `Document` objects or a compatible internal structure), each containing text and relevant metadata, ready for embedding and graph extraction.

- **Key Stages & Components:**
    1.  **Data Acquisition & Initial Processing (Source-Specific):**
        *   **For Google Drive Documents (PDF, DOCX, etc.):**
            *   `GDriveFileFetcher`: Uses `GDriveReader.download_file_to_path()` to get the file.
            *   `ComplexFileProcessor`: Uses `DocumentParser.aparse_file()` (which internally uses LlamaParse). This step handles both text extraction from complex formats AND initial chunking into LlamaIndex `Document` objects, along with metadata extraction by LlamaParse.
        *   **For YouTube Transcripts:**
            *   `YouTubeTranscriptFetcher`: The FastAPI backend endpoint will call the `mcp2_get_transcript` tool, providing the YouTube URL. This tool returns the transcript as plain text.
            *   `PlainTextProcessor`: 
                *   Takes the raw transcript text.
                *   Applies a text chunking strategy (e.g., using `RecursiveCharacterTextSplitter` or similar, configured to produce reasonably sized chunks for embedding and context).
                *   For each chunk, creates a LlamaIndex `Document` object (or a compatible structure), manually populating its `text` attribute and `metadata` attribute (e.g., with `source_url: youtube_video_url`, `source_type: youtube_transcript`, `chunk_number`).

    2.  **Embedding (Common for all processed chunks):**
        *   `EmbeddingGenerator`: Iterates through the list of `Document` objects (or chunks) produced by the previous stage.
        *   For each chunk, extracts its text content.
        *   Uses `CustomGeminiEmbedding._get_text_embedding()` (as defined in `src.graph_querying.embedding_utils.py` and configured via `config.yaml`) to generate a 1536-dimensional embedding.
        *   Associates the embedding with the chunk and its metadata.

    3.  **Graph Extraction (Common for all processed chunks):**
        *   `KnowledgeGraphExtractor`: Iterates through the list of `Document` objects (or chunks).
        *   For each chunk, extracts its text content.
        *   Uses `GraphExtractor.extract()` (from `graphiti-core`, configured with `universal_ontology.py`) to identify entities and relationships, associating them with the `group_id`.

    4.  **Storage (Common for all processed data):**
        *   `DataStorer`:
            *   Uses `ChromaIngester` to store the text chunks, their embeddings, and metadata (including `group_id`) into ChromaDB.
            *   Uses Neo4j client logic (as in `ingest_gdrive_documents.py`) to store the extracted graph data (nodes, relationships with `group_id`) into Neo4j.

- **FastAPI Endpoint Orchestration:**
    *   The `/ingest_gdrive_documents` endpoint will orchestrate: `GDriveFileFetcher` -> `ComplexFileProcessor` -> `EmbeddingGenerator` -> `KnowledgeGraphExtractor` -> `DataStorer`.
    *   The `/ingest_youtube_transcript` endpoint will orchestrate: `YouTubeTranscriptFetcher` (which includes the `mcp2_get_transcript` call) -> `PlainTextProcessor` -> `EmbeddingGenerator` -> `KnowledgeGraphExtractor` -> `DataStorer`.
    *   This modular design allows for different initial processing paths while reusing common downstream components for embedding, graph extraction, and storage.

## 4. Technical & Architectural Considerations

### 4.1. UI Framework
- **Streamlit**: Primary choice for rapid development and Python integration. The application will be structured as a multi-page Streamlit app if necessary (e.g., Chat, Ingestion).

### 4.2. Backend API (FastAPI)
- **Purpose**: Decouple Streamlit UI from core logic, enabling easier testing, maintenance, and potential future UI changes (e.g., to Google ADK Web Chat UI).
- **Key Endpoints**:
    - `/chat`: Input (user query, conversation history). This endpoint will now orchestrate the full "Super Hybrid Query Orchestration" (Section 3.6), including parallel retrieval, fusion, re-ranking, and finally answer synthesis. Output (streaming synthesized answer, graph data for visualization from the Neo4j/Graphiti path, comprehensive source attribution data from both ChromaDB and Neo4j/Graphiti).
    - `/list_gdrive_files`: Input (GDrive folder ID), Output (list of files).
    - `/ingest_gdrive_documents`: Input (list of GDrive file IDs, target `group_id`), Output (ingestion status).
    - `/ingest_youtube_transcript`: Input (YouTube URL, target `group_id`), Output (ingestion status).
- **Authentication**: For this personal use project, API endpoints will initially be unsecured. Future ADK/MCP integration might introduce auth.

### 4.3. Graph Visualization Library
- **Primary Recommendation**: `streamlit-agraph` due to its native Streamlit feel and `vis.js` backend.
- **Alternative**: `pyvis` if `streamlit-agraph` proves limiting. Output HTML from `pyvis` can be embedded using `st.components.v1.html`.
- **Data Flow**: The FastAPI `/chat` endpoint will return a JSON structure containing nodes and edges from `GraphitiNativeSearcher` results, which Streamlit will then pass to the chosen visualization library.

## 5. Future-Proofing: Agent & MCP Integration

This architecture, with a FastAPI backend exposing distinct functionalities, is designed for future agentic systems using the **Google Agent Development Kit (ADK)** and the **Model Context Protocol (MCP)**.

- **Modular Tools via FastAPI Endpoints**: Each FastAPI endpoint (chat, GDrive listing, ingestion) effectively acts as a callable 'tool'.
- **MCP Server Readiness**: These FastAPI endpoints can be straightforwardly wrapped or exposed by one or more **MCP Servers**.
    - Example: An `IngestionControlMCPServer` could expose `/list_gdrive_files`, `/ingest_gdrive_documents`, and `/ingest_youtube_transcript`.
    - The `/chat` endpoint itself, which orchestrates search and synthesis, could be a tool for a higher-level agent.
- **MCP Client**: The Streamlit UI (or a future ADK Web Chat UI) acts as an **MCP Client** by making HTTP requests to these FastAPI endpoints (which could, in turn, be fronting MCP Servers).

This ensures that core logic (search via `GraphitiNativeSearcher`, ingestion via `GDriveReader` & `GraphExtractor`, LLM interactions via `google-genai` SDK) remains modular and accessible for future agent-based orchestration.

## 6. Out of Scope for this Phase

- Full implementation of ADK agents or direct MCP server/client bindings beyond the API abstraction.
- Advanced, persistent, graph-based conversational memory (e.g., Zep/Graphiti integration for memory).
- User authentication, accounts, and multi-user support for the Streamlit app.
- Deployment to a production cloud environment (focus remains on a robust local prototype).
- Local file system browsing for ingestion (prioritizing Google Drive).

## 7. Success Criteria

- A user can open the Streamlit application, ask a question in the chat interface, and receive a synthesized, natural-language answer.
- The Streamlit UI successfully renders an interactive graph visualization relevant to the user's query, using data from `GraphitiNativeSearcher`.
- The user can inspect the sources (graph elements or text chunks) that contributed to the answer within the Streamlit UI.
- The user can navigate to a 'Data Ingestion' section in Streamlit, list files from a Google Drive folder, select GDrive files for ingestion, OR provide a YouTube URL and trigger its transcript's ingestion.
- The backend ingestion pipeline is refactored for modularity, allowing steps like parsing to be skipped for sources like YouTube transcripts.
- The backend `/chat` endpoint successfully implements the "Super Hybrid Query Orchestration", demonstrably using results from both ChromaDB (semantic chunk search) and Neo4j/Graphiti (graph-aware search) to generate answers.
- Source attribution in the UI clearly differentiates between evidence sourced from ChromaDB and Neo4j/Graphiti.
- The backend is architected with a clean FastAPI layer, separating UI from the core logic (search orchestration, ingestion, LLM synthesis).
- Conversational context (recent turns) is passed to the backend to improve follow-up question handling.
