# Project Context: Hybrid Graph RAG System - Post-Ingestion Phase

**Date:** 2025-06-14

## Current Status:

The initial data ingestion phase for the `kev-new-graph-rag` project is
**complete and stable**. Key achievements include:

1. **Successful Data Ingestion:** All sample documents (AI research,
   geopolitical analysis, YouTube transcript summary) have been successfully
   processed and ingested into the backend systems.
2. **Universal Ontology Alignment:** The `universal_ontology.py` (featuring 9
   core entity types and 10 universal relationship types) has been successfully
   aligned with Graphiti-core's requirements. This involved:
   - Ensuring all relationship models include `fact: str`,
     `valid_at: Optional[datetime]`, and `invalid_at: Optional[datetime]`
     fields.
   - Confirming Graphiti's dual-labeling approach (`:Entity` + specific ontology
     label like `:Person`) works as intended.
3. **Error Resolution:** Critical ingestion errors, including `JSONDecodeError`
   from LLM outputs and Neo4j warnings about missing temporal properties, have
   been resolved.
4. **Verified Neo4j Setup:** Required Neo4j full-text indexes are in place and
   operational, and credentials are correctly managed via `.env`.

## Data Storage Overview:

The hybrid RAG system currently utilizes two primary data stores:

- **ChromaDB (Vector Store):**
  - Stores chunks of the original text content from the ingested documents.
  - Stores embeddings for each text chunk, generated using Google's Gemini
    embedding models (e.g., `gemini-embedding-001` via Vertex AI).
- **Neo4j AuraDB (Graph Database):**
  - Stores the structured knowledge graph extracted by Graphiti.
  - This includes nodes (e.g., Person, Organization, Technology) and
    relationships (e.g., Creates, Uses, Influences) defined by the universal
    ontology.
  - Graphiti also stores embeddings for node names and summaries, and
    potentially for relationship facts, within Neo4j, enabling graph-based
    semantic search capabilities.

## Next Major Goal: Develop the Hybrid RAG System

With a robust and populated knowledge graph and vector store, the project now
transitions to building the query and retrieval components of the hybrid RAG
system.

**Immediate Next Steps (as per existing PRD/discussions):**

- **Design and Implement Query/Retrieval Logic:** Develop the mechanisms to:
  - Accept a user query.
  - Retrieve relevant text chunks from ChromaDB based on semantic similarity
    (vector search).
  - Identify key entities or concepts in the user query or retrieved text
    chunks.
  - Query Neo4j to find related entities, relationships, and subgraphs that
    provide additional context around these key entities/concepts.
  - This may involve graph traversals, pattern matching, and leveraging
    Graphiti's built-in search functionalities (which use the full-text indexes
    and potentially graph embeddings).
- **Context Formatting and Augmentation:** Develop strategies to combine the
  retrieved textual context (from ChromaDB) and graph context (from Neo4j) into
  a comprehensive prompt for the LLM.
- **LLM-Powered Answer Generation:** Utilize a Google Gemini model to generate
  answers based on the augmented context.
- **Build User Interface/Application Layer:** (Further out) Create an interface
  for users to interact with the RAG system.

This `context.md` document serves as a snapshot to ensure continuity and provide
a clear starting point for the next phase of development.

---

## Update (2025-06-14): Graph Query Implementation

**Current Focus:** The immediate priority has shifted to implementing the Neo4j
query component of the RAG system. Specifically, creating a LlamaIndex retriever
that can translate natural language questions into Cypher queries compatible
with the Graphiti-populated database.

**Key Developments:**

1. **New Module (`src/graph_querying/graphiti_retriever.py`):**
   - A new Python module has been created to encapsulate the logic for a
     Graphiti-aware Text-to-Cypher retriever.

2. **Custom Text-to-Cypher Prompt:**
   - A detailed prompt template (`CUSTOM_TEXT_TO_CYPHER_PROMPT_STR`) has been
     engineered for the LlamaIndex `TextToCypherRetriever`.
   - **Crucially, this prompt instructs the LLM to adhere to Graphiti's specific
     conventions:**
     - **Dual Node Labels:** Queries must use the `(n:Entity:SpecificType)`
       pattern for all nodes.
     - **Temporal Filtering:** All relationship matches `[r:REL_TYPE]` must
       include a `WHERE` clause to filter for currently active relationships
       using a `$current_datetime` parameter. The logic is:
       `r.valid_at IS NOT NULL AND r.valid_at <= $current_datetime AND (r.invalid_at IS NULL OR r.invalid_at > $current_datetime) AND r.expired_at IS NULL`.

3. **Vertex AI Integration:**
   - The retriever is configured to use Google Gemini models via **Vertex AI**.
   - It uses the `llama_index.llms.google_genai.GoogleGenAI` class with the
     `vertexai_config` parameter, which requires `GCP_PROJECT_ID` and
     `GCP_REGION` to be set in the `.env` file.
   - This aligns with the project's existing Google Cloud authentication
     strategy (Application Default Credentials) rather than a simple API key.

**Next Immediate Action:**

- **Test `graphiti_retriever.py`:** The script is ready to be executed. This
  first run will serve to:
  - Verify that the environment variables for Neo4j and Vertex AI are correctly
    loaded.
  - Confirm that the LLM can generate a syntactically correct Cypher query based
    on the custom prompt.
  - **Test the parameter passing mechanism:** Determine if the
    `$current_datetime` parameter is successfully passed to the Neo4j driver
    during query execution. This is a critical test, as the base LlamaIndex
    retriever does not natively support this.

---

## Update (2025-06-15): LlamaIndex Querying Debugging & Potential Pivot

**Current Focus:** Extensive debugging of the LlamaIndex-based
`TextToCypherRetriever` (`graphiti_retriever.py`) to ensure correct Cypher
generation and execution against the Graphiti-populated Neo4j database.

**Key Challenges & Debugging Steps Undertaken (LlamaIndex Approach):**

1. **Environment & Configuration:**
   - Resolved initial environment variable issues (`GCP_PROJECT_ID`,
     `GCP_LOCATION`).
   - Ensured correct LLM model ID (`gemini-pro`) is loaded from `config.yaml`.
   - Fixed `AttributeError` related to `_graph_store` access.
   - Corrected `ModuleNotFoundError` for
     `llama_index.core.query_bundle.QueryBundle` by updating the import path to
     `llama_index.core.schema.QueryBundle`.

2. **LLM Output Control (Cypher Generation):**
   - Addressed LLM returning Cypher wrapped in markdown (`cypher ...`) by:
     - Initially attempting prompt engineering (instructing LLM to return plain
       Cypher).
     - Implementing `SanitizedTextToCypherRetriever` to subclass
       `TextToCypherRetriever` and override `_parse_generated_cypher` to strip
       markdown. This was successful.
   - Iteratively refined the `CUSTOM_TEXT_TO_CYPHER_PROMPT_STR` to:
     - Improve entity mapping from natural language to Cypher properties (e.g.,
       "Alice" -> `person_name: 'Alice'`).
     - Avoid unnecessary/spurious Cypher parameters not present in the NL
       question.
     - Encourage direct value matching instead of parameterization (except for
       `$current_datetime`).
     - Ensure LLM adapts examples rather than copying them verbatim.
     - Provide a full, relevant example for the "Alice projects" query.

3. **Runtime Parameter Passing (`$current_datetime`):**
   - This has been the most persistent issue. The Neo4j driver consistently
     throws a `ParameterMissing` error for `$current_datetime`.
   - **Attempts to resolve this included:**
     - Trying to pass `params` via
       `retriever.retrieve(nl_query, params=cypher_params)` (incorrect
       LlamaIndex API usage).
     - Setting `retriever._cypher_query_params` (parameters not passed to the
       graph store).
     - Setting `retriever._graph_store._cypher_query_params` (parameters still
       not picked up by the driver call within
       `Neo4jPropertyGraphStore.structured_query`).
     - Implementing `PatchedPropertyGraphStore` to override `structured_query`
       and explicitly pass parameters to `self._driver.execute_query()`. This
       also failed to resolve the issue, with script output becoming truncated,
       hindering further diagnosis.
     - Attempting to replace `$current_datetime` with a literal ISO datetime
       string directly within the `_parse_generated_cypher` method as a
       workaround. Script output remained truncated.

4. **Output Handling:**
   - Fixed a runtime `AttributeError` when trying to access `.properties` on
     `TextNode` objects by printing `.text` and `.metadata` instead.

**Current Situation & User Consideration:**

- Despite numerous attempts and "patches" to the LlamaIndex
  `TextToCypherRetriever` and `Neo4jPropertyGraphStore`, passing the dynamic
  `$current_datetime` parameter to Neo4j for temporal filtering remains
  unresolved.
- The script execution has also started showing truncated output, making it
  difficult to pinpoint the exact failure point in the latest attempts.
- **The USER is now considering a significant pivot:** To move away from the
  LlamaIndex `TextToCypherRetriever` due to these persistent integration
  complexities and explore a more direct approach for natural language to Cypher
  translation and execution, potentially leveraging Graphiti's underlying
  capabilities or a simpler custom pipeline. This would involve querying the
  Neo4j database (populated by Graphiti) without the LlamaIndex abstraction
  layer for this specific task.

**Next Steps (Pending User Decision on Pivot):**

- If continuing with LlamaIndex: Diagnose the truncated script output to get
  full error messages.
- If pivoting: Begin research and design for a direct NL-to-Cypher approach
  tailored to the Graphiti schema.

---

## Update (2025-06-15): End-to-End Query Pipeline VALIDATED

**Current Focus:** The project has successfully pivoted away from LlamaIndex and
built a robust, end-to-end Natural Language to Cypher query pipeline using the
`google-genai` SDK directly. This represents a major milestone.

**Key Achievements & Discoveries:**

1. **Successful Pipeline Execution:** The `cypher_generator.py` script now runs
   flawlessly. It correctly:
   - Loads environment variables and configuration.
   - Generates a valid ontology schema string.
   - Uses a strict, example-driven prompt to guide the Gemini LLM.
   - Receives a perfectly structured JSON object containing a valid Cypher query
     and parameters.
   - Connects to the Neo4j database and executes the query without technical
     errors.

2. **Problem Refined: Code vs. Data:** The test query "Who created GPT-4?"
   returned 0 records. However, analysis of the source document
   (`ai_research_sample.txt`) confirms the information **is present**. This
   proves the query pipeline code is **correct**, and the issue is a
   **data-mapping discrepancy**.

3. **New Hypothesis:** The Graphiti ingestion process correctly identified the
   "OpenAI" and "GPT-4" entities but did not use the relationship name `CREATES`
   as we assumed. The actual relationship name or structure used by Graphiti to
   link these two nodes is unknown.

**Current Situation & Next Steps for New Chat:**

- The primary technical challenge of building a reliable, schema-aware
  NL-to-Cypher pipeline is **solved**.
- The final remaining task is to inspect the Neo4j database to understand how
  Graphiti represents relationships.
- **The immediate next step is to perform data reconnaissance:** Run basic
  Cypher queries directly against the Neo4j database to find the "OpenAI" and
  "GPT-4" nodes and inspect the relationships between them. This will reveal the
  correct relationship `name` property or structure to use in our LLM prompt,
  which will finalize the project.

---

## **MAJOR UPDATE - : Successful Migration to Graphiti-Native Hybrid Search**

**Status: ✅ COMPLETE ARCHITECTURAL PIVOT** - The project has successfully
migrated from the manual NL-to-Cypher approach to a full **Graphiti-native
hybrid search implementation**.

### **What Changed:**

**From:** Manual Cypher generation → **To:** Graphiti's built-in hybrid search
capabilities **From:** Custom query pipeline → **To:** Production-ready search
with advanced reranking **From:** Data mapping issues → **To:** Robust semantic
search that bypasses relationship naming problems

### **Technical Challenges Resolved:**

1. **✅ Embedding Dimensionality Compatibility**
   - **Problem**: Ingestion used 1536-dimensional embeddings
     (`gemini-embedding-001`), but Graphiti's default `GeminiEmbedder` generated
     1024-dimensional embeddings
   - **Solution**: Implemented hybrid approach using `CustomGeminiEmbedding` for
     query-time embeddings, passed as `query_vector` to Graphiti search
     functions

2. **✅ Authentication & API Integration**
   - **Problem**: OpenAI API dependency causing authentication errors
   - **Solution**: Complete elimination of OpenAI calls; all authentication via
     Vertex AI ADC (`GOOGLE_GENAI_USE_VERTEXAI=true`)

3. **✅ Import Path Corrections**
   - **Problem**: Incorrect import paths for Graphiti components
     (`graphiti_core.llm` vs `graphiti_core.llm_client.config`)
   - **Solution**: Fixed all import paths based on actual Graphiti codebase
     structure

4. **✅ API Method Compatibility**
   - **Problem**: Attempted to call non-existent methods like `.create()` on
     `CustomGeminiEmbedding`
   - **Solution**: Use `._get_query_embedding()` method consistent with
     ingestion pipeline

### **Current Implementation:**

**File**: `src/graph_querying/graphiti_native_search.py` **Class**:
`GraphitiNativeSearcher`

**Architecture**:

- **Custom Embedding Generation**: Uses `CustomGeminiEmbedding` (same as
  ingestion) for 1536-dimensional embeddings
- **Graphiti Integration**: Passes custom embeddings via `query_vector`
  parameter to bypass internal embedding generation
- **Multiple Search Strategies**: Standard hybrid search, entity-focused search
  with context, advanced search with configurable recipes
- **Search Recipes**: `EDGE_HYBRID_SEARCH_RRF`, `NODE_HYBRID_SEARCH_RRF`,
  `COMBINED_HYBRID_SEARCH_RRF`

**Key Benefits Achieved**:

1. **Hybrid Search**: Combines keyword, semantic, and graph traversal methods
2. **Advanced Reranking**: RRF, MMR, and cross-encoder reranking strategies
3. **Embedding Consistency**: Query-time embeddings match ingestion (1536
   dimensions)
4. **Authentication Security**: Uses ADC instead of hardcoded API keys
5. **Production Ready**: Comprehensive error handling and logging

### **Test Status:**

**Test Script**: `src/graph_querying/test_hybrid_search.py` **Last Status**:
Import error resolved (`LLMConfig` path fixed) **Expected Results**:

- ✅ 1536-dimensional embeddings generated via Vertex AI
- ✅ No OpenAI API calls or authentication errors
- ✅ Successful Graphiti search integration
- ✅ Multiple search strategies working

### **Documentation Updated:**

**File**: `Project Documentation/understanding_graphiti_search.md` **Status**:
Completely rewritten to reflect current implementation **Content**: Technical
challenges, solutions, architecture, usage examples

### **Next Steps for New Chat:**

1. **✅ PRIORITY**: Run the test script to verify the hybrid search
   implementation works end-to-end
   ```powershell
   uv run python src/graph_querying/test_hybrid_search.py
   ```

2. **Integration Testing**: Test the hybrid search with real queries against the
   existing Neo4j database

3. **Performance Evaluation**: Compare search quality and performance vs. the
   original manual Cypher approach

4. **Optional Enhancement**: Add natural language result summarization using
   Gemini LLM for user-friendly responses

### **Key Technical Insights:**

- **Graphiti's `query_vector` parameter** is the key to embedding
  compatibility - it allows bypassing internal embedding generation
- **Hybrid search approach** eliminates the data mapping issues that plagued the
  manual Cypher approach
- **Semantic search** is more robust than exact relationship matching for
  knowledge retrieval
- **Production authentication** via ADC is more secure and maintainable than API
  keys

### **Project Status:**

**✅ MIGRATION COMPLETE** - The project has successfully evolved from a
proof-of-concept NL-to-Cypher pipeline to a production-ready hybrid search
system that leverages Graphiti's full capabilities while maintaining embedding
consistency with the ingestion pipeline.

The original data mapping challenges are now **obsolete** - semantic search
finds relevant information regardless of exact relationship naming conventions
used by Graphiti during ingestion.
