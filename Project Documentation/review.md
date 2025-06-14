# Review: Custom Text-to-Cypher Prompt & Implementation Plan

## 1. Draft Custom `text_to_cypher_template`

This template is designed to guide the Google Gemini LLM to generate Cypher queries that are compliant with Graphiti's specific conventions.

```text
Given an input question, convert it to a Cypher query.
You must only use the provided schema and not infer any node labels or relationship types not explicitly listed.
The Neo4j graph you are querying is managed by Graphiti and has specific conventions:

1.  **Node Labels:** Nodes always have a general ':Entity' label AND a specific entity type label. For example, a person node is queried as `(p:Entity:Person)`, an organization as `(o:Entity:Organization)`. Refer to the 'Node Labels' section in the schema below for available specific types.

2.  **Relationship Temporal Validity:** All relationships `[r:REL_TYPE]` must be filtered to include only those currently active. To do this, you MUST append the following conditions to every relationship in your Cypher query, using the provided `$current_datetime` parameter:
    `WHERE r.valid_at IS NOT NULL AND r.valid_at <= $current_datetime AND (r.invalid_at IS NULL OR r.invalid_at > $current_datetime) AND r.expired_at IS NULL`
    If a relationship variable is already part of a WHERE clause for other conditions, append these temporal conditions using AND. If a relationship is matched but has no other specific conditions, you must still add this temporal WHERE clause.

3.  **Property Names:** Use the exact property names as defined in the 'Node Properties' and 'Relationship Properties' sections of the schema.

**Schema:**
---------------------
{schema}
---------------------

**Instructions:**
-   Generate a Cypher query.
-   Ensure all matched relationships `[r:REL_TYPE]` include the temporal validity WHERE clause mentioned in point 2.
-   Ensure all matched nodes use the dual-label convention mentioned in point 1 (e.g., `(n:Entity:SpecificType)`).
-   Use the `$current_datetime` parameter as provided for temporal filtering. The value for `$current_datetime` will be an ISO 8601 timestamp string (e.g., "2025-06-14T14:41:54-05:00").

**Question:** {query_str}
**Cypher Query:**
```

## 2. Implementation Plan Outline

1.  **Prepare the Graph Schema for LlamaIndex:**
    *   Ensure your `Neo4jPropertyGraphStore` provides an accurate schema string for the `{schema}` placeholder. This must include:
        *   Specific node labels (e.g., "Person", "Organization").
        *   Relationship types (e.g., "WORKS_AT").
        *   Ontology-correct property names for each node and relationship (e.g., `person_name`).

2.  **Instantiate `TextToCypherRetriever` with the Custom Prompt:**
    *   Create a `PromptTemplate` from the custom string.
    *   Initialize the `TextToCypherRetriever`, passing the `graph_store`, `llm`, and the custom `text_to_cypher_template`.
    ```python
    from llama_index.core.indices.property_graph import TextToCypherRetriever
    from llama_index.core.prompts import PromptTemplate
    from llama_index.llms.google_genai import GoogleGenAI
    from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

    # Custom prompt template string
    custom_prompt_str = """... (the template text from above) ..."""
    custom_prompt = PromptTemplate(custom_prompt_str)

    # Initialize components
    graph_store = Neo4jPropertyGraphStore(...)
    llm = GoogleGenAI(model_name="models/gemini-pro")

    # Instantiate retriever with the custom prompt
    text_to_cypher_retriever = TextToCypherRetriever(
        graph_store=graph_store,
        llm=llm,
        text_to_cypher_template=custom_prompt,
        verbose=True
    )
    ```

3.  **Handling the `$current_datetime` Parameter:**
    *   The generated Cypher will contain the `$current_datetime` parameter.
    *   The component executing the query (likely the `Neo4jPropertyGraphStore`) must be given the value for this parameter.
    *   The `query` method of the graph store typically accepts a `params` dictionary.
    *   The execution flow must be configured to pass `{"current_datetime": "YYYY-MM-DDTHH:MM:SSZ"}` with each query. This may require customizing a retriever or query engine class if the parameter passing isn't straightforward through the abstraction layers.

4.  **Integration into `RouterQueryEngine`:**
    *   Wrap the configured `TextToCypherRetriever` (or a query engine built from it) into a `QueryEngineTool`.
    *   This tool becomes one of the choices for your `RouterQueryEngine`, allowing the router to select graph search when appropriate.

5.  **Testing and Iteration:**
    *   Use `verbose=True` to inspect the generated Cypher.
    *   Verify that the dual-label and temporal clauses are correctly applied.
    *   Iteratively refine the prompt based on LLM performance.
