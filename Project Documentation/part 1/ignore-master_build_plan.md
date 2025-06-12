# Master Build Plan: Comprehensive Graph RAG System

This document outlines the detailed tasks and subtasks for building the Comprehensive Graph RAG System, as specified in the `technical_prd.md`. Each main task concludes with a unit testing subtask to ensure functionality and robustness. Progress will be tracked by checking off completed items.

**Legend**:
- `[ ]` To Do
- `[x]` Completed
- `[-]` Skipped/Not Applicable

## Phase 1: Core Graph RAG MVP & Basic Agentic Capabilities

### Task 1.1: Environment Setup & Configuration
*   **Status**: Completed
*   **Subtasks**:
    - [x] 1.1.1. Initialize local Git repository.
    - [x] 1.1.2. Set up Python virtual environment using `uv`.
    - [x] 1.1.3. Create `pyproject.toml` for project metadata and dependencies.
    - [x] 1.1.4. Create `src/.env` with placeholders for API keys and credentials (e.g., `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `GOOGLE_API_KEY`, `USE_PARALLEL_RUNTIME` (optional for Neo4j optimization), and other LLM API keys as needed).
    - [x] 1.1.5. Create comprehensive `.gitignore` file (including `src/.env`, `.venv/`, IDE files, OS files, logs).
    - [x] 1.1.6. Create initial project documentation structure (`Project Documentation/` with `technical_prd.md`, `buildprogress.md`, `description.txt`, `master_build_plan.md`).
    - [x] 1.1.7. Create private GitHub repository (`Kevin-Graph-RAG`).
    - [x] 1.1.8. Perform initial commit and push to remote repository (`master` branch).
    - [x] 1.1.9. Unit Test: Verify environment, Git setup, and that sensitive files are ignored. (Effectively done via manual checks and `git ls-files` for `.env`).

### Task 1.2: Neo4j AuraDB Connection
*   **Status**: Completed
*   **Subtasks**:
    - [x] 1.2.1. **Research**: Briefly check for any recent updates or best practices for `neo4j` Python driver and AuraDB interactions.
    - [x] 1.2.2. Add `neo4j` and `python-dotenv` to `pyproject.toml` and install using `uv add`.
    - [x] 1.2.3. Create `scripts/test_neo4j_connection.py`.
    - [x] 1.2.4. Implement logic in script to load Neo4j credentials (URI, user, password, database) from `src/.env`.
    - [x] 1.2.5. Implement logic to establish a connection to Neo4j AuraDB using `GraphDatabase.driver`.
    - [x] 1.2.6. Implement `driver.verify_connectivity()` to confirm connection.
    - [x] 1.2.7. Implement a simple test query (e.g., `MERGE` a test node, `RETURN` its properties, then `DELETE` it) to verify operational status.
    - [x] 1.2.8. Run the script and confirm successful connection and query execution, including proper error handling for connection/auth issues.
    - [x] 1.2.9. Unit Test: Manual test verification of the script's output is acceptable for this task.

### Task 1.3: Basic Graphiti-core Integration & Initial Data Ingestion
*   **Status**: In Progress
*   **Framework Focus**: **Graphiti** (primary), **Neo4j** (storage)
*   **Subtasks**:
    - [x] 1.3.1. **Research**: Review latest `graphiti-core` documentation for episodic knowledge graph model, data ingestion methods, and temporal graph features. Note any breaking changes or new recommendations.
    - [x] 1.3.2. Add `graphiti-core[google-genai]` to `pyproject.toml` and install using `uv add`.
    - [ ] 1.3.3. ~~Define initial Pydantic models~~ -> Understand Graphiti's episodic data model, which uses episodes as primary units of information that automatically generate entities and relationships.
    - [x] 1.3.4. Create a Python script (`scripts/graphiti_ingest_test.py`) to:
        - [x] 1.3.4.1. Initialize Graphiti's `Graph` object with Neo4j connection details from `.env`.
        - [x] 1.3.4.2. Create sample episodes with test data in both text and JSON formats.
        - [x] 1.3.4.3. Use `graph.add_episode()` to ingest episodes into Neo4j with appropriate parameters (name, episode_body, source, source_description, reference_time).
        - [x] 1.3.4.4. Verify data ingestion by querying Neo4j directly through `graph.driver.session()` for the ingested episodes, nodes, relationships, and their properties.
        - [x] 1.3.4.5. Implement cleanup logic and proper error handling for test data after verification.
    - [ ] 1.3.5. Explore Graphiti's advanced features:
        - [ ] 1.3.5.1. Implement bulk ingestion using `add_episode_bulk()` for batched processing of multiple episodes.
        - [ ] 1.3.5.2. Test multi-tenant or domain-specific graph segmentation using namespaces (`group_id` parameter).
        - [ ] 1.3.5.3. Explore custom entity types and relationship extraction from episodes.
    - [ ] 1.3.6. Unit Test: Write unit tests for the episodic data ingestion script. Test different episode types (text, JSON, message), verify proper entity extraction, and ensure error handling for connection issues.

### Task 1.4: Llama-Index Knowledge Graph Construction
*   **Status**: To Do
*   **Framework Focus**: **Llama-Index** (primary), **Neo4j** (storage), **Gemini** (LLM)
*   **Rationale**: While Graphiti handles temporal KG management, Llama-Index provides specialized text-to-KG extraction capabilities that complement Graphiti's strengths.
*   **Subtasks**:
    - [ ] 1.4.1. **Research**: Review latest `Llama-Index` documentation for `KnowledgeGraphIndex`, `Neo4jGraphStore`, LLM integration (especially with Gemini), and best practices for KG construction.
    - [ ] 1.4.2. Add `llama-index`, `llama-index-graph-stores-neo4j`, `llama-index-llms-gemini`, and any other necessary Llama-Index sub-packages to `pyproject.toml` and install.
    - [ ] 1.4.3. Create a script (`scripts/llama_kg_construction_test.py`).
    - [ ] 1.4.4. Prepare sample text documents for ingestion (e.g., 2-3 short paragraphs in a list or small text files).
    - [ ] 1.4.5. Configure Llama-Index `ServiceContext` (or `Settings`) with Gemini as the LLM and an appropriate embedding model.
    - [ ] 1.4.6. Initialize `Neo4jGraphStore` with credentials and connect to your AuraDB instance.
    - [ ] 1.4.7. Construct a `KnowledgeGraphIndex` using the sample documents, `Neo4jGraphStore`, and the configured `ServiceContext`.
    - [ ] 1.4.8. Inspect the Neo4j database (via Browser or Cypher queries) to verify the structure of the graph created by Llama-Index (nodes, relationships, properties like `text`, `label`, `embedding` if applicable).
    - [ ] 1.4.9. Unit Test: Write unit tests for the KG construction script. Mock `LLM` calls, `Neo4jGraphStore` interactions, and document loading to verify the logic of entity/relationship extraction and graph element creation.

### Task 1.5: Llama-Index Hybrid Search & Retrieval
*   **Status**: To Do
*   **Framework Focus**: **Llama-Index** (primary), **Neo4j** (storage)
*   **Rationale**: Llama-Index provides mature hybrid retrieval patterns that combine semantic and graph-based search, which is essential for effective RAG over knowledge graphs.
*   **Subtasks**:
    - [ ] 1.5.1. **Research**: Review `Llama-Index` documentation for vector indexing (e.g., `VectorStoreIndex`), hybrid retrieval strategies (e.g., combining KG and vector search), and relevant retriever classes.
    - [ ] 1.5.2. Ensure Llama-Index vector store capabilities are configured. For MVP, an in-memory `SimpleVectorStore` or `Neo4jVectorStore` (if using Neo4j for embeddings) can be used.
    - [ ] 1.5.3. In a new script (`scripts/llama_hybrid_search_test.py`) or extending the previous one:
        - [ ] 1.5.3.1. Create a `VectorStoreIndex` from the sample documents.
        - [ ] 1.5.3.2. Set up a retriever that combines results from the `KnowledgeGraphIndex` (keyword/graph path search) and the `VectorStoreIndex` (semantic search).
        - [ ] 1.5.3.3. Perform sample queries (natural language) and evaluate the retrieved nodes/text chunks for relevance and diversity.
    - [ ] 1.5.4. Experiment with different retriever configurations and fusion methods if available.
    - [ ] 1.5.5. Unit Test: Write unit tests for the hybrid retrieval logic. Mock index/retriever calls and verify that the combination and ranking of results are processed as expected.

### Task 1.6: Llama-Index Natural Language Querying (KG RAG)
*   **Status**: To Do
*   **Framework Focus**: **Llama-Index** (primary), **Gemini** (LLM), **Neo4j** (storage)
*   **Rationale**: Llama-Index excels at text2cypher translation and RAG query engines, complementing Graphiti's knowledge representation capabilities.
*   **Subtasks**:
    - [ ] 1.6.1. **Research**: Review `Llama-Index` documentation for query engines, especially `KnowledgeGraphQueryEngine` or general RAG pipelines, prompt engineering for KG RAG, and response synthesis.
    - [ ] 1.6.2. In a script (`scripts/llama_kg_rag_test.py`):
        - [ ] 1.6.2.1. Load the `KnowledgeGraphIndex` (from Task 1.4) and `VectorStoreIndex` (from Task 1.5).
        - [ ] 1.6.2.2. Configure a query engine (e.g., a RAG pipeline using the hybrid retriever from Task 1.5, or `KnowledgeGraphQueryEngine` if suitable).
        - [ ] 1.6.2.3. Ensure Gemini Pro 2.5 is used for response synthesis.
        - [ ] 1.6.2.4. Pose natural language questions designed to be answerable from the ingested knowledge graph and documents.
        - [ ] 1.6.2.5. Evaluate the generated responses for accuracy, coherence, and evidence of using graph context.
        - [ ] 1.6.2.6. (Optional) Inspect any intermediate Cypher queries generated by Llama-Index if the query engine exposes them.
    - [ ] 1.6.3. Refine prompts or query engine configurations if necessary to improve response quality.
    - [ ] 1.6.4. Unit Test: Write unit tests for the KG RAG query engine. Mock LLM calls, retriever outputs, and graph queries to ensure the query construction, context retrieval, and response synthesis logic works as expected.

### Task 1.7: Gemini Pro 2.5 Integration for Advanced Reasoning (Deep Dive)
*   **Status**: To Do
*   **Framework Focus**: **Gemini** (primary), **Graphiti** and **Llama-Index** (integration)
*   **Rationale**: Gemini provides advanced reasoning capabilities that enhance both Graphiti's episodic processing and Llama-Index's RAG patterns.
*   **Subtasks**:
    - [ ] 1.7.1. **Research**: Deep dive into Gemini Pro 2.5 documentation, especially its capabilities for structured output, function calling/tool use, and advanced reasoning modes relevant to RAG.
    - [ ] 1.7.2. Ensure proper environment configuration for Gemini API access:
        - [ ] 1.7.2.1. Set up `GOOGLE_API_KEY` in the `.env` file for direct API access.
        - [ ] 1.7.2.2. Configure Graphiti to use Gemini via `graphiti-core[google-genai]` extension.
        - [ ] 1.7.2.3. Set up Llama-Index integration with `llama-index-llms-gemini` if using both frameworks.
    - [ ] 1.7.3. Create specialized reasoning modules that leverage Gemini's capabilities:
        - [ ] 1.7.3.1. Implement graph traversal and path reasoning using Gemini's structured output.
        - [ ] 1.7.3.2. Develop entity relationship analysis capabilities to extract insights from the knowledge graph.
    - [ ] 1.7.4. Experiment with Gemini's "thinking mode" or chain-of-thought prompting for complex multi-step reasoning over the graph.
    - [ ] 1.7.5. Integrate with Graphiti's querying capabilities while minimizing direct LLM client imports in core functionality.
    - [ ] 1.7.6. Unit Test: Write unit tests for the integration modules with proper mocking of Gemini API calls.

### Task 1.8: Streamlit MVP Chat Interface
*   **Status**: To Do
*   **Framework Focus**: **Streamlit** (primary), **Llama-Index** (query engine), **Graphiti** (knowledge access)
*   **Rationale**: Streamlit provides the user interface layer that connects to both Llama-Index for querying and Graphiti for knowledge graph operations.
*   **Subtasks**:
    - [ ] 1.8.1. **Research**: Review `Streamlit` documentation for chat elements (`st.chat_input`, `st.chat_message`), session state management, and best practices for building interactive applications.
    - [ ] 1.8.2. Add `streamlit` to `pyproject.toml` and install.
    - [ ] 1.8.3. Create a Streamlit application file (e.g., `app/main_app.py` in a new `app` directory).
    - [ ] 1.8.4. Design a simple UI with:
        - [ ] 1.8.4.1. A persistent chat input field at the bottom of the screen.
        - [ ] 1.8.4.2. A display area for chat history (user queries and LLM responses).
    - [ ] 1.8.5. Integrate the Llama-Index KG RAG query engine (from Task 1.6, using Gemini) into the Streamlit app's backend logic.
    - [ ] 1.8.6. Implement session state to store and manage conversation history.
    - [ ] 1.8.7. Ensure user queries are passed to the query engine and responses are displayed in the chat interface.
    - [ ] 1.8.8. Run the Streamlit app (`uv run streamlit run app/main_app.py`) and test the chat flow.
    - [ ] 1.8.9. Unit Test: Write unit tests for the backend logic/callback functions of the Streamlit app (e.g., the function that calls the Llama-Index query engine). Mock Llama-Index calls and Streamlit's session state where appropriate. UI testing can be manual for the MVP.

### Task 1.9: Basic ADK Agent for Orchestration (Optional for MVP)
*   **Status**: To Do
*   **Framework Focus**: **Google ADK** (primary), **Llama-Index** and **Graphiti** (orchestrated frameworks)
*   **Rationale**: ADK provides the agent orchestration layer that coordinates between Llama-Index querying capabilities and Graphiti's knowledge management.
*   **Subtasks**:
    - [ ] 1.9.1. **Research**: Review Google ADK documentation for agent creation, service invocation, and integration with Python applications.
    - [ ] 1.9.2. Add Google ADK (`google-apphosting-sdk` or specific packages) to `pyproject.toml` and install.
    - [ ] 1.9.3. Define a simple ADK agent that encapsulates the Llama-Index KG RAG query engine.
        - [ ] 1.9.3.1. The agent should expose a method to receive a user query.
        - [ ] 1.9.3.2. Internally, this method calls the Llama-Index query engine.
        - [ ] 1.9.3.3. The agent returns the result.
    - [ ] 1.9.4. (Optional) Explore ADK's capabilities for managing multi-turn conversations or state if it simplifies the Streamlit integration.
    - [ ] 1.9.5. Modify the Streamlit app (Task 1.8) to interact with the ADK agent instead of directly calling the Llama-Index query engine.
    - [ ] 1.9.6. Unit Test: Write unit tests for the ADK agent's core logic, mocking the Llama-Index query engine call.

### Task 1.10: Basic MCP Tool Integration (Optional for MVP)
*   **Status**: To Do
*   **Framework Focus**: **MCP** (primary), **Google ADK** (integration)
*   **Rationale**: MCP tools extend the capabilities of the ADK agent with specialized functions not natively available in Llama-Index or Graphiti.
*   **Subtasks**:
    - [ ] 1.10.1. **Research**: Review MCP documentation and identify a simple, available tool (or create a mock MCP tool server) for integration (e.g., a tool that provides current date/time, or a very basic web search).
    - [ ] 1.10.2. If using ADK (Task 1.9), define the MCP tool for the ADK agent according to ADK's tool integration mechanisms.
    - [ ] 1.10.3. Modify the agent/query processing logic to include a step where it decides if the tool should be used (e.g., based on keywords in the query, or if the KG RAG system returns a low-confidence answer).
    - [ ] 1.10.4. Implement logic to call the MCP tool and incorporate its results into the final response presented to the user.
    - [ ] 1.10.5. Unit Test: Write unit tests for the tool usage logic. Mock MCP client calls and tool responses to verify the decision-making process and result integration.

## Phase 2: Advanced Features & Refinements (High-Level - Subtasks to be detailed later)

**Note on Framework Integration**: In Phase 2, we'll build on the complementary relationship established between our frameworks:
- **Graphiti**: Will continue to manage temporal aspects and episodic data processing.
- **Llama-Index**: Will handle retrieval patterns and LLM orchestration.
- **Neo4j**: Will serve as the persistent graph storage layer.
- **Gemini**: Will provide reasoning and generation capabilities across the system.
- [ ] Task 2.1: Multi-modal RAG (Text, Images, potentially Code).
- [ ] Task 2.2: Advanced Agentic Behavior (Proactive Retrieval, Complex Task Decomposition).
- [ ] Task 2.3: Federated Knowledge Graph Capabilities.
- [ ] Task 2.4: Enhanced UI/UX and Visualization (e.g., graph visualizations in Streamlit).
- [ ] Task 2.5: Robust Error Handling, Logging, and Monitoring.
- [ ] Task 2.6: Performance Optimization and Scalability Testing.
- [ ] Task 2.7: Comprehensive Security Review (especially if considering deployment).

---
**Note**: This Master Build Plan is a living document and may be updated as the project progresses and new insights are gained. `buildprogress.md` will track progress against this plan.
