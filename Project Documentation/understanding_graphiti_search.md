# Understanding Graphiti's Native Search Capabilities

This document outlines the findings from reviewing the `graphiti-core` library's search functionality and details how the `kev-new-graph-rag` project will leverage these capabilities for its natural language to Cypher query pipeline.

## Key Graphiti Modules and Files Analyzed:

1.  **`graphiti_core/graphiti.py`**: Defines the main `Graphiti` class, which is the primary entry point for interacting with the library.
2.  **`graphiti_core/search/search.py`**: Contains the core search orchestration logic.
3.  **`graphiti_core/search/search_filters.py`**: Defines the `SearchFilters` class used for filtering search results.
4.  **`graphiti_core/search/search_config.py`** and **`graphiti_core/search/search_config_recipes.py`**: Define search configurations and pre-set recipes for different search strategies.

## Core Search Functionality in Graphiti:

### 1. The `Graphiti` Class (`graphiti.py`)

*   **`Graphiti.search(query: str, center_node_uuid: Optional[str], group_ids: Optional[List[str]], num_results: int, search_filter: Optional[SearchFilters]) -> str`**:
    *   This is the main public method for performing searches.
    *   It takes a natural language `query` string.
    *   It can optionally take a `center_node_uuid` for context or reranking, `group_ids` for namespacing/multi-tenancy, a `num_results` limit, and a `SearchFilters` object.
    *   The default search configuration used is `COMBINED_HYBRID_SEARCH_CROSS_ENCODER`.
    *   **Crucially, the docstring indicates it returns "the edges as a string," suggesting it's designed to return a textual summary or facts derived from relevant graph elements rather than raw Cypher or structured graph objects directly from this top-level method.**
*   **`Graphiti._search(query: str, config: SearchConfig, ...)`**:
    *   A deprecated but underlying method called by `Graphiti.search()`.
    *   It accepts a more detailed `SearchConfig` object, allowing for finer control over the search process.
    *   This method delegates to the `search()` function in `graphiti_core/search/search.py`.

### 2. Search Orchestration (`search/search.py`)

*   **`async def search(clients: GraphitiClients, query: str, group_ids: Optional[List[str]], config: SearchConfig, search_filter: SearchFilters, ...)`**:
    *   This is the core function that orchestrates the actual search.
    *   It first generates a query vector from the input `query` string using the configured `EmbedderClient`.
    *   It then concurrently performs searches across different graph element types:
        *   `edge_search()`
        *   `node_search()`
        *   `episode_search()`
        *   `community_search()`
    *   The results from these individual searches are then combined and returned as a `SearchResults` object.
*   **Specialized Search Functions (e.g., `edge_search`, `node_search`)**:
    *   Each of these functions implements a multi-stage search process:
        1.  **Candidate Retrieval**: Utilizes various methods based on the `SearchConfig`:
            *   `*_fulltext_search()`: For keyword-based matching against relevant text fields.
            *   `*_similarity_search()`: For semantic matching using vector embeddings.
            *   `*_bfs_search()`: For Breadth-First Search graph traversal from specified origin nodes (if `bfs_origin_node_uuids` is provided).
        2.  **Reranking**: Applies reranking algorithms to the combined candidates from the retrieval step. Common rerankers include:
            *   `rrf()` (Reciprocal Rank Fusion)
            *   `maximal_marginal_relevance()` (MMR)
            *   Cross-encoder based reranking (using `CrossEncoderClient`)
            *   `node_distance_reranker()` (based on graph distance to a `center_node_uuid`)
    *   These functions return lists of Pydantic model instances (e.g., `List[EntityEdge]`, `List[EntityNode]`).
*   **Output**: The top-level `search()` function in this module returns a `SearchResults` object. This object is a Pydantic model containing:
    *   `edges: List[EntityEdge]`
    *   `nodes: List[EntityNode]`
    *   `episodes: List[EpisodicNode]`
    *   `communities: List[CommunityNode]`

### 3. Filtering (`search/search_filters.py`)

*   **`SearchFilters(BaseModel)`**: This Pydantic model allows for detailed filtering criteria to be applied during the search process. Key filterable fields include:
    *   `node_labels: Optional[List[str]]`
    *   `edge_types: Optional[List[str]]`
    *   **Temporal Properties**: These are crucial for the project's requirements.
        *   `valid_at: Optional[List[List[DateFilter]]]`
        *   `invalid_at: Optional[List[List[DateFilter]]]`
        *   `created_at: Optional[List[List[DateFilter]]]`
        *   `expired_at: Optional[List[List[DateFilter]]]`
    *   The temporal filters accept a list of lists of `DateFilter` objects. `DateFilter` itself contains a `date: datetime` and a `comparison_operator: ComparisonOperator` (e.g., equals, greater_than, less_than_equal).
    *   This structure allows for complex AND/OR logic for date conditions (inner list is AND, outer list is OR).
*   **Filter Query Constructors (`node_search_filter_query_constructor`, `edge_search_filter_query_constructor`)**:
    *   These functions take a `SearchFilters` object and dynamically construct Cypher `WHERE` clause snippets and parameter dictionaries. These snippets are then incorporated into the underlying Cypher queries executed by the various search methods (e.g., full-text, similarity searches within Neo4j).

## Summary of Graphiti's Native Search:

Graphiti's native search is a powerful hybrid system designed to retrieve relevant **graph elements (nodes, edges, episodes, communities)** based on a natural language query and specified filters. It combines keyword search, semantic (vector) search, and graph traversal (BFS), followed by sophisticated reranking.

**Importantly, Graphiti's `search()` method does not directly translate a natural language query into a full, executable Cypher query for arbitrary graph patterns. Instead, it retrieves existing graph elements that are deemed relevant to the query.**

## Project-Specific Approach for NL-to-Cypher

Given Graphiti's capabilities, the `kev-new-graph-rag` project will adopt the following approach for its NL-to-Cypher pipeline:

1.  **Schema Generation for LLM Context**: 
    *   The `src.graph_querying.schema_utils.get_ontology_schema_string()` function will be used to generate a detailed markdown representation of the `universal_ontology.py` (node types, relationship types, properties, and temporal considerations like `$current_datetime`).

2.  **Optional Candidate Retrieval (Graphiti Search)**:
    *   For complex queries or when needing to ground the LLM with specific entities, Graphiti's `search()` method *can* be used as an initial step.
    *   The user's natural language query, along with any `group_id` or high-level temporal hints (if discernible directly from the NL query), can be passed to `Graphiti.search()` with appropriate `SearchFilters`.
    *   The `SearchResults` (containing relevant nodes/edges) can provide valuable context (e.g., names, types, UUIDs of specific entities) to the LLM for the next step.
    *   This step is optional and can be bypassed if the NL query is simple enough or if a direct NL-to-Cypher translation is preferred for certain query types.

3.  **LLM-Powered Cypher Generation (Gemini)**:
    *   The core NL-to-Cypher translation will be handled by a Google Gemini LLM accessed via the `google-genai` SDK.
    *   The prompt to Gemini will include:
        *   The original natural language query from the user.
        *   The comprehensive ontology schema string (from `schema_utils.py`).
        *   Optionally, context from Graphiti's search results (if step 2 was performed), such as names or UUIDs of relevant entities.
        *   Clear instructions to generate a Cypher query and a corresponding dictionary of parameters.
    *   **Structured Output**: Gemini's structured output feature will be used, with a Pydantic model defining the expected response format (e.g., a model with fields like `cypher_query: str` and `parameters: Dict[str, Any]`).
    *   The LLM will be explicitly instructed to:
        *   Use the `$current_datetime` parameter for temporal filtering based on `valid_at` and `invalid_at` properties on relationships (e.g., `r.valid_at <= $current_datetime AND (r.invalid_at IS NULL OR r.invalid_at > $current_datetime)` for currently active relationships).
        *   Adhere to the provided ontology for node labels, relationship types, and property names.

4.  **Cypher Query Execution**:
    *   The Python application will receive the structured output (Cypher query and parameters) from Gemini.
    *   It will inject the actual `datetime.now(timezone.utc)` value for the `$current_datetime` parameter.
    *   The finalized Cypher query will be executed against the Neo4j AuraDB instance using the standard Neo4j Python driver.

This approach leverages Graphiti's strengths in retrieving relevant graph elements and filtering, while relying on the advanced reasoning capabilities of Gemini LLMs for constructing precise, temporally-aware Cypher queries based on the project's specific ontology.
