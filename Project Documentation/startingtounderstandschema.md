# Understanding the Graphiti-Generated Neo4j Schema

This document outlines our current, empirically-verified understanding of how Graphiti translates our Pydantic-based universal ontology into a concrete Neo4j graph schema. This understanding is based on clearing the database, running the `ingest_gdrive_documents.py` script, and directly inspecting the resulting nodes and relationships in Neo4j.

## 1. Node Schema

Our investigation confirms that Graphiti uses the `CamelCase` Pydantic class names from our ontology directly as Neo4j node labels.

- **Pydantic Model**: `class Person(Entity): ...`
- **Neo4j Label**: `Person`

This is the expected and desired behavior. Graphiti also adds its own internal labels for organization, such as `__Node__`, `__Entity__`, and `Entity`, which appears to be a parent label for all our custom entity types.

## 2. Relationship Schema

This was the most critical discovery. Instead of creating a unique relationship type for each Pydantic relationship class, Graphiti uses a more generic and flexible model.

- **Generic Relationship Type**: The primary relationship type created is `RELATES_TO`.
- **Semantic Meaning Storage**: The specific semantic meaning of the relationship (e.g., that a person *creates* content) is stored as a **property** on the `RELATES_TO` relationship.

### Key Relationship Properties:

- `name`: This property holds the specific relationship type. The value is the `UPPER_SNAKE_CASE` version of the original Pydantic relationship class name.
  - **Pydantic Model**: `class HasCreator(Creates): ...`
  - **Neo4j Relationship**: `(:Content)-[r:RELATES_TO {name: 'HAS_CREATOR'}]->(:Person)`
- `fact`: A natural language string describing the specific relationship instance (e.g., "Crash Course (Hank Green & John Green)").
- `uuid`: A unique identifier for the relationship instance.
- `source_node_uuid` / `target_node_uuid`: UUIDs linking back to the source and target nodes.
- `created_at` / `valid_at`: Temporal properties, as expected from the Graphiti documentation, for tracking when the relationship was created and when it is considered valid.

## 3. Implications for Cypher Query Generation

This schema has direct implications for our `cypher_generator.py` module:

1.  **LLM Prompt**: The system prompt must be updated to describe this schema accurately. It needs to instruct the LLM to use the `RELATES_TO` type and filter by the `name` property for semantic queries.
2.  **Cypher Queries**: All generated Cypher queries must now follow this pattern: `MATCH (a:NodeTypeA)-[r:RELATES_TO {name: 'RELATIONSHIP_NAME'}]->(b:NodeTypeB)`.
3.  **`EDGE_TYPE_MAP`**: The `EDGE_TYPE_MAP` in our script remains useful, but it must map the `(Source, Target)` tuple to the correct `UPPER_SNAKE_CASE` string that will be used in the `{name: ...}` property filter.

This understanding aligns with advanced graph modeling practices that prevent schema bloat and maintain flexibility. We are now confident in proceeding with the necessary updates to our query generation logic.
