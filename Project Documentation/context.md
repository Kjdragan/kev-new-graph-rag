# Project Context: Hybrid Graph RAG System - Post-Ingestion Phase

**Date:** 2025-06-14

## Current Status:

The initial data ingestion phase for the `kev-new-graph-rag` project is **complete and stable**. Key achievements include:

1.  **Successful Data Ingestion:** All sample documents (AI research, geopolitical analysis, YouTube transcript summary) have been successfully processed and ingested into the backend systems.
2.  **Universal Ontology Alignment:** The `universal_ontology.py` (featuring 9 core entity types and 10 universal relationship types) has been successfully aligned with Graphiti-core's requirements. This involved:
    *   Ensuring all relationship models include `fact: str`, `valid_at: Optional[datetime]`, and `invalid_at: Optional[datetime]` fields.
    *   Confirming Graphiti's dual-labeling approach (`:Entity` + specific ontology label like `:Person`) works as intended.
3.  **Error Resolution:** Critical ingestion errors, including `JSONDecodeError` from LLM outputs and Neo4j warnings about missing temporal properties, have been resolved.
4.  **Verified Neo4j Setup:** Required Neo4j full-text indexes are in place and operational, and credentials are correctly managed via `.env`.

## Data Storage Overview:

The hybrid RAG system currently utilizes two primary data stores:

*   **ChromaDB (Vector Store):**
    *   Stores chunks of the original text content from the ingested documents.
    *   Stores embeddings for each text chunk, generated using Google's Gemini embedding models (e.g., `gemini-embedding-001` via Vertex AI).
*   **Neo4j AuraDB (Graph Database):**
    *   Stores the structured knowledge graph extracted by Graphiti.
    *   This includes nodes (e.g., Person, Organization, Technology) and relationships (e.g., Creates, Uses, Influences) defined by the universal ontology.
    *   Graphiti also stores embeddings for node names and summaries, and potentially for relationship facts, within Neo4j, enabling graph-based semantic search capabilities.

## Next Major Goal: Develop the Hybrid RAG System

With a robust and populated knowledge graph and vector store, the project now transitions to building the query and retrieval components of the hybrid RAG system.

**Immediate Next Steps (as per existing PRD/discussions):**

*   **Design and Implement Query/Retrieval Logic:** Develop the mechanisms to:
    *   Accept a user query.
    *   Retrieve relevant text chunks from ChromaDB based on semantic similarity (vector search).
    *   Identify key entities or concepts in the user query or retrieved text chunks.
    *   Query Neo4j to find related entities, relationships, and subgraphs that provide additional context around these key entities/concepts.
    *   This may involve graph traversals, pattern matching, and leveraging Graphiti's built-in search functionalities (which use the full-text indexes and potentially graph embeddings).
*   **Context Formatting and Augmentation:** Develop strategies to combine the retrieved textual context (from ChromaDB) and graph context (from Neo4j) into a comprehensive prompt for the LLM.
*   **LLM-Powered Answer Generation:** Utilize a Google Gemini model to generate answers based on the augmented context.
*   **Build User Interface/Application Layer:** (Further out) Create an interface for users to interact with the RAG system.

This `context.md` document serves as a snapshot to ensure continuity and provide a clear starting point for the next phase of development.

---

## Update (2025-06-14): Graph Query Implementation

**Current Focus:** The immediate priority has shifted to implementing the Neo4j query component of the RAG system. Specifically, creating a LlamaIndex retriever that can translate natural language questions into Cypher queries compatible with the Graphiti-populated database.

**Key Developments:**

1.  **New Module (`src/graph_querying/graphiti_retriever.py`):**
    *   A new Python module has been created to encapsulate the logic for a Graphiti-aware Text-to-Cypher retriever.

2.  **Custom Text-to-Cypher Prompt:**
    *   A detailed prompt template (`CUSTOM_TEXT_TO_CYPHER_PROMPT_STR`) has been engineered for the LlamaIndex `TextToCypherRetriever`.
    *   **Crucially, this prompt instructs the LLM to adhere to Graphiti's specific conventions:**
        *   **Dual Node Labels:** Queries must use the `(n:Entity:SpecificType)` pattern for all nodes.
        *   **Temporal Filtering:** All relationship matches `[r:REL_TYPE]` must include a `WHERE` clause to filter for currently active relationships using a `$current_datetime` parameter. The logic is: `r.valid_at IS NOT NULL AND r.valid_at <= $current_datetime AND (r.invalid_at IS NULL OR r.invalid_at > $current_datetime) AND r.expired_at IS NULL`.

3.  **Vertex AI Integration:**
    *   The retriever is configured to use Google Gemini models via **Vertex AI**.
    *   It uses the `llama_index.llms.google_genai.GoogleGenAI` class with the `vertexai_config` parameter, which requires `GCP_PROJECT_ID` and `GCP_REGION` to be set in the `.env` file.
    *   This aligns with the project's existing Google Cloud authentication strategy (Application Default Credentials) rather than a simple API key.

**Next Immediate Action:**

*   **Test `graphiti_retriever.py`:** The script is ready to be executed. This first run will serve to:
    *   Verify that the environment variables for Neo4j and Vertex AI are correctly loaded.
    *   Confirm that the LLM can generate a syntactically correct Cypher query based on the custom prompt.
    *   **Test the parameter passing mechanism:** Determine if the `$current_datetime` parameter is successfully passed to the Neo4j driver during query execution. This is a critical test, as the base LlamaIndex retriever does not natively support this.
