# Understanding Graphiti's Native Search Capabilities

This document outlines the findings from reviewing the `graphiti-core` library's search functionality and details how the `kev-new-graph-rag` project leverages these capabilities for its hybrid search implementation.

**Status: ✅ IMPLEMENTED AND TESTED** - As of December 2024, we have successfully implemented a full hybrid search integration using Graphiti's native search capabilities with custom Gemini embeddings.

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

*   **`async def search(clients: GraphitiClients, query: str, group_ids: Optional[List[str]], config: SearchConfig, search_filter: SearchFilters, query_vector: Optional[List[float]] = None, ...)`**:
    *   This is the core function that orchestrates the actual search.
    *   **Key Discovery**: The `query_vector` parameter allows passing pre-computed embeddings, bypassing internal embedding generation.
    *   It first generates a query vector from the input `query` string using the configured `EmbedderClient` (unless `query_vector` is provided).
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
    *   `group_ids: Optional[List[str]]` (for multi-tenancy)
    *   `valid_at: Optional[datetime]` (for temporal filtering)
    *   `invalid_at: Optional[datetime]` (for temporal filtering)
    *   `center_node_uuid: Optional[str]` (for context-aware reranking)
    *   And several others...

*   **Filter Utility Functions**: The module also contains utility functions like `build_node_filters()` and `build_edge_filters()` that translate the high-level `SearchFilters` object into concrete Cypher query fragments.
    *   These functions take a `SearchFilters` object and dynamically construct Cypher `WHERE` clause snippets and parameter dictionaries. These snippets are then incorporated into the underlying Cypher queries executed by the various search methods (e.g., full-text, similarity searches within Neo4j).

## Technical Challenges Resolved

### 1. Embedding Dimensionality Compatibility ✅

**Challenge**: The ingestion pipeline used `CustomGeminiEmbedding` with 1536-dimensional embeddings (`gemini-embedding-001`), but Graphiti's default `GeminiEmbedder` was generating 1024-dimensional embeddings, causing Neo4j compatibility issues.

**Solution**: 
- Use `CustomGeminiEmbedding` for query-time embedding generation (matching ingestion)
- Pass generated embeddings as `query_vector` parameter to Graphiti's search functions
- This bypasses Graphiti's internal embedding generation entirely, avoiding dimensionality conflicts

### 2. Authentication with Vertex AI ADC ✅

**Challenge**: Ensuring all API calls use Application Default Credentials (ADC) instead of direct API keys.

**Solution**:
- Configure environment variables: `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`
- Use `genai.Client()` with ADC authentication in both custom embeddings and Graphiti LLM client
- Avoid hardcoded API keys in production code

### 3. API Method Compatibility ✅

**Challenge**: Initial implementation attempted to call non-existent methods like `.create()` on `CustomGeminiEmbedding`.

**Solution**: 
- Use `._get_query_embedding()` method to match ingestion pipeline usage
- Ensure consistent method calls across ingestion and query-time embedding generation

### 4. OpenAI API Dependency Elimination ✅

**Challenge**: Graphiti was defaulting to OpenAI embeddings when `embedder=None`, causing authentication errors.

**Solution**:
- Pass pre-computed embeddings via `query_vector` parameter
- Set `embedder=None` in Graphiti initialization since we provide embeddings directly
- This completely eliminates OpenAI API calls from the search pipeline

### 5. Graphiti's Built-in Gemini Integration ✅

**Discovery**: Graphiti includes a built-in Gemini integration in `graphiti_core/embedders/gemini.py` that supports configurable embedding models and dimensions.

**Key Parameters**:
- `GeminiEmbedderConfig` supports:
  - `embedding_model`: Default is 'embedding-001', can be set to 'gemini-embedding-001'
  - `embedding_dim`: Default is 1024, can be set to 1536 to match our Neo4j database
  - `api_key`: Optional, can be None to use ADC authentication

**Future Opportunity**: 
While our current implementation uses a custom embedding class for compatibility with the ingestion pipeline, we could potentially simplify by using Graphiti's built-in `GeminiEmbedder` with proper configuration for both ingestion and query processes. This would eliminate the need for our custom embedding class while maintaining dimensional compatibility.

## Current Implementation: Hybrid Search with Graphiti

Our production implementation (`src/graph_querying/graphiti_native_search.py`) provides a complete hybrid search solution:

### Architecture

```python
class GraphitiNativeSearcher:
    """
    Hybrid search implementation using:
    - CustomGeminiEmbedding for 1536-dimensional query embeddings 
    - Graphiti's native search, reranking, and filtering capabilities
    - Search recipes for different search strategies
    """
```

### Key Components

1. **Custom Embedding Generation**:
   - Uses `CustomGeminiEmbedding` (same as ingestion pipeline)
   - Generates 1536-dimensional embeddings via `gemini-embedding-001`
   - Authenticates via Vertex AI ADC

2. **Graphiti Integration**:
   - Initializes `Graphiti` with `GeminiClient` for LLM operations
   - Sets `embedder=None` to avoid internal embedding generation
   - Passes custom embeddings via `query_vector` parameter

3. **Search Methods**:
   - `hybrid_search()`: Standard hybrid search with RRF reranking
   - `entity_focused_search()`: Context-aware search with center node reranking
   - `advanced_search()`: Configurable search with different recipe strategies

4. **Search Recipes Used**:
   - `EDGE_HYBRID_SEARCH_RRF`: Hybrid edge search with Reciprocal Rank Fusion
   - `NODE_HYBRID_SEARCH_RRF`: Hybrid node search with RRF
   - `COMBINED_HYBRID_SEARCH_RRF`: Combined search across all element types
   - Alternative BM25-based recipes for different ranking strategies

### Testing and Validation

**Test Script**: `src/graph_querying/test_hybrid_search.py`

**Test Results**: 
- ✅ Embedding compatibility test passes (1536 dimensions confirmed)
- ✅ No OpenAI API calls (eliminated authentication errors)
- ✅ Successful Vertex AI authentication and embedding generation
- ✅ Graphiti search integration working with custom embeddings
- ✅ Multiple search strategies tested (standard, entity-focused, advanced)

### Sample Usage

```python
async with GraphitiNativeSearcher() as searcher:
    # Standard hybrid search
    results = await searcher.hybrid_search(
        query="What is artificial intelligence?",
        num_results=10
    )
    
    # Entity-focused search with context
    results = await searcher.entity_focused_search(
        query="AI research trends",
        center_node_uuid="some-entity-uuid", 
        num_results=5
    )
    
    # Advanced search with specific recipe
    results = await searcher.advanced_search(
        query="machine learning frameworks",
        recipe_name="COMBINED_HYBRID_SEARCH_RRF",
        num_results=8
    )
```

## Summary of Current Approach

**Graphiti's native search is now fully integrated** as the primary search mechanism for the `kev-new-graph-rag` project. Unlike the original theoretical approach that considered Graphiti as optional candidate retrieval, we now use it as the complete search solution.

**Key Benefits Achieved**:
1. **Hybrid Search**: Combines keyword, semantic, and graph traversal search methods
2. **Advanced Reranking**: Uses RRF, MMR, and cross-encoder reranking strategies  
3. **Embedding Consistency**: Query-time embeddings match ingestion pipeline (1536 dimensions)
4. **Authentication Security**: Uses ADC instead of hardcoded API keys
5. **Search Flexibility**: Multiple search recipes and filtering options
6. **Production Ready**: Comprehensive error handling and logging

**This implementation provides a robust, scalable search foundation** that can be extended with additional natural language interfaces or integrated with LLM-powered query expansion and result summarization as needed.

## Migration from Manual Cypher Approach

The project has successfully migrated from:
- ❌ **Manual Cypher generation** with custom NL-to-Cypher translation
- ❌ **Direct Neo4j driver usage** with hand-crafted queries
- ❌ **Embedding dimension mismatches** and authentication issues

To:
- ✅ **Graphiti-native hybrid search** with proven algorithms
- ✅ **Consistent embedding pipeline** across ingestion and query
- ✅ **Enterprise-grade authentication** via ADC
- ✅ **Comprehensive search capabilities** with filtering and reranking

This migration provides a more robust, maintainable, and feature-rich search experience while maintaining full compatibility with the existing knowledge graph structure.
