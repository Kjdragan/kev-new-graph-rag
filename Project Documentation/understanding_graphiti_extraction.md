# Understanding Graphiti's Temporal Features and Entity Labeling

This document outlines the revised understanding of Graphiti-core's handling of temporal properties on relationships and its use of a generic `:Entity` label, based on a review of the `graphiti_core` codebase and examples. It also proposes an updated approach for aligning the `universal_ontology.py` with Graphiti's requirements.

## 1. Graphiti's Handling of Temporal Properties

Graphiti-core has a robust system for managing the temporal lifecycle of relationships, primarily `RELATES_TO` edges. This system revolves around three key properties:

*   **`valid_at`**: Represents the date and time when a relationship became true or started. The LLM is prompted to extract this as an ISO 8601 string based on the text content and a reference timestamp.
*   **`invalid_at`**: Represents the date and time when a relationship stopped being true or ended. Similar to `valid_at`, the LLM is prompted to extract this as an ISO 8601 string.
*   **`expired_at`**: This property is largely managed internally by Graphiti. It can be set programmatically if an `invalid_at` date is provided, or if Graphiti's edge contradiction logic determines that an existing edge has been superseded by new information.

**Key Mechanisms:**

*   **LLM Prompts**: The prompt engineering within Graphiti (e.g., `graphiti_core/prompts/extract_edges.py`) explicitly instructs the LLM to return `valid_at` and `invalid_at` as part of the JSON structure for extracted edges.
*   **Parsing**: Graphiti internally parses these date strings from the LLM response into `datetime` objects (e.g., in `graphiti_core/utils/maintenance/edge_operations.py` and `graphiti_core/utils/maintenance/temporal_operations.py`).
*   **Internal Models**: Graphiti's internal `EntityEdge` Pydantic model includes `valid_at: Optional[datetime]`, `invalid_at: Optional[datetime]`, and `expired_at: Optional[datetime]`.
*   **Indexing and Search**: These temporal properties are used in creating Neo4j indexes (e.g., `valid_at_edge_index`, `invalid_at_edge_index`) and are available for filtering in search operations.

## 2. Graphiti's Use of the `:Entity` Label

The generic `:Entity` label is fundamental to many of Graphiti's core functionalities:

*   **Indexing**: A significant number of Neo4j indexes, including b-tree indexes on `uuid`, `group_id`, `name`, `created_at`, and the critical full-text index `node_name_and_summary`, are specifically defined `FOR (n:Entity)`.
*   **Cypher Queries**: Internal Cypher queries for data manipulation (clearing data), graph algorithms (community detection), search utilities (for nodes and edges), and various node/edge management operations consistently use the `:Entity` label to match relevant nodes.
*   **Node Creation**: Crucially, Graphiti's node creation mechanism (e.g., in `graphiti_core/models/nodes/node_db_queries.py`) employs a Cypher pattern like:
    ```cypher
    MERGE (n:Entity {uuid: node_data.uuid})
    SET n += node_data.properties
    SET n:{node_data.label} 
    ```
    This ensures that every node managed by Graphiti receives the base `:Entity` label first, and then its specific ontology label (e.g., `:Person`, `:Organization`) is added. This dual labeling is key, as it allows our specific ontology types to function correctly while ensuring compatibility with Graphiti's core operations that depend on `:Entity`.

## 3. Aligning `universal_ontology.py` with Graphiti

Based on the findings, the following adjustments are needed in our `universal_ontology.py` to ensure seamless integration with Graphiti:

*   **Temporal Properties in Relationship Models**:
    *   The `universal_ontology.py` currently defines `valid_from` and `valid_to` in its relationship models. These must be changed.
    *   All Pydantic models representing relationships (e.g., `RelatesTo` and any other types intended for use in `graphiti_instance.add_episode`) should define:
        *   `valid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact became true or started. Use ISO 8601 format if providing as string input to LLM.")`
        *   `invalid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact stopped being true or ended. Use ISO 8601 format if providing as string input to LLM.")`
    *   It is not necessary to add `expired_at` to our ontology's relationship Pydantic models, as Graphiti manages this internally.
*   **Node Models**: Node models should continue to be simple Pydantic classes inheriting from `pydantic.BaseModel`. Graphiti will automatically handle the addition of the `:Entity` label alongside the specific labels defined in the ontology (e.g., `Person`, `Organization`).

## 4. Implications for JSON Malformed Error

The previous `JSONDecodeError` encountered with `geopolitical_analysis_sample.txt` was hypothesized to be due to a mismatch between the LLM's output and Graphiti's parsing expectations. The LLM is prompted to return `valid_at` and `invalid_at` (as strings). If our ontology defined `valid_from`/`valid_to`, this discrepancy could confuse the LLM or cause it to generate JSON that doesn't perfectly align with the structure Graphiti expects for temporal properties, leading to parsing failures.

By renaming `valid_from` to `valid_at` and `valid_to` to `invalid_at` in our `universal_ontology.py` relationship models, and ensuring their descriptions align with Graphiti's intent, we provide clearer and more consistent signals to the LLM. This alignment is expected to improve the reliability of the JSON output for edges and resolve the parsing errors.

## 5. Conclusion and Revised Approach

Graphiti-core has well-defined mechanisms for temporal data management and relies on a generic `:Entity` label for its core graph operations and indexing. Our project's `universal_ontology.py` can be made fully compatible by:

1.  **Renaming and Retyping Temporal Fields**: In all relationship models within `universal_ontology.py`, change `valid_from` to `valid_at` and `valid_to` to `invalid_at`, ensuring they are `Optional[datetime] = None` and their descriptions are consistent with Graphiti's usage.
2.  **Leveraging Dual Labeling**: Continue defining specific node types (Person, Organization, etc.) in the ontology. Graphiti will ensure these nodes also receive the `:Entity` label, making them compatible with its internal systems and indexes.

No modifications to the Graphiti-core codebase are necessary or advisable. The successful resolution of ingestion errors by aligning `universal_ontology.py` (specifically adding `fact`, `valid_at`, and `invalid_at` to relationships) confirmed this approach.

## 6. Additional Lessons Learned and Best Practices

Beyond the specific fixes for temporal properties and the `:Entity` label, this process highlighted several broader lessons for working effectively with Graphiti and building a robust knowledge graph ingestion pipeline:

*   **Ontology as LLM Schema:**
    *   The Pydantic models defined in your ontology (e.g., `universal_ontology.py`) serve as a direct schema or blueprint for Graphiti's LLM-based extraction. The LLM will attempt to populate the fields you define.
    *   For node entities, defining a comprehensive set of `Optional` properties allows for flexibility while guiding the LLM to extract desired structured information.
    *   For relationship entities, the `fact: str` field is crucial for capturing the rich, nuanced context of the connection. This is highly beneficial for RAG systems that rely on detailed textual context.
    *   Adding more structured properties to relationships (beyond `fact`, `valid_at`, `invalid_at`) is a trade-off. It can enable more precise, structured queries but may reduce the flexibility offered by a descriptive `fact` string. Evaluate this based on specific downstream RAG query needs.

*   **Iterative Ontology Refinement:**
    *   Expect to iterate on your ontology. Initial designs may need adjustments based on LLM behavior, Graphiti's specific requirements (as seen with temporal properties), or the nuances of your source data.
    *   Start with a core set of entities and relationships, test ingestion, and refine. The successful update to include `fact`, `valid_at`, and `invalid_at` in all universal relationships is a testament to this iterative process.

*   **Troubleshooting Ingestion Errors:**
    *   **Isolate Failing Documents:** When errors occur (like the `JSONDecodeError`), attempt to reprocess only the problematic document. This helps determine if the error is transient (e.g., an LLM hiccup) or persistent (pointing to content or schema issues).
    *   **Verify Neo4j Indexes:** Ensure all required Neo4j full-text and property indexes are correctly created and online. The `verify_neo4j_indexes.py` script was invaluable for this.
    *   **Examine Logs Carefully:** Graphiti and your ingestion script logs provide crucial clues. The absence of Neo4j warnings after ontology changes confirmed the fix for temporal properties.
    *   **Graphiti's Abstraction:** While Graphiti abstracts direct LLM interaction, understanding its expected input/output (e.g., JSON structure for edges, including temporal fields) is key to diagnosing issues.

*   **Adherence to Graphiti's API and Model:**
    *   As highlighted in previous project memories (MEMORY[11381b00-35db-4c7d-864f-1f5ee2fb135f]), strict adherence to Graphiti's API (e.g., parameters for `add_episode`) and internal data model constraints (e.g., reserved attribute names, expected Pydantic base models) is paramount.

## 7. Neo4j Credentialing and Setup

Properly configuring access to your Neo4j database is essential for the ingestion pipeline and any subsequent query operations. This project utilizes Neo4j AuraDB, but similar principles apply to local instances.

*   **Required Credentials:**
    *   `NEO4J_URI`: The connection URI for your Neo4j instance. For AuraDB, this typically starts with `neo4j+s://` or `bolt+s://` and includes the unique database identifier.
    *   `NEO4J_USER`: The username for accessing the database. For AuraDB, this is often `neo4j` by default, but can be other users you create.
    *   `NEO4J_PASSWORD`: The password associated with the `NEO4J_USER`.

*   **Source of Credentials:**
    *   **Neo4j AuraDB:** These credentials (URI, default username, and password) are provided in your AuraDB instance console after the database is created. You can also create additional users with specific roles and passwords through the Aura console or Cypher commands.
    *   **Local Neo4j Instance:** When setting up a local Neo4j server (e.g., via Neo4j Desktop or Docker), you typically define the initial password for the `neo4j` user during setup. The URI is usually `bolt://localhost:7687` by default.

*   **Secure Management with `.env`:**
    *   It is critical **not to hardcode** these credentials directly into your scripts.
    *   This project uses a `.env` file at the project root to store these sensitive values.
    *   The `python-dotenv` library (typically invoked via `load_dotenv()` at the beginning of scripts like `ingest_gdrive_documents.py` and `verify_neo4j_indexes.py`) is used to load these environment variables into the application's runtime environment, making them accessible via `os.getenv()`.
    *   Ensure your `.env` file is included in your `.gitignore` file to prevent accidental commitment of credentials to version control.

*   **Consistency:** Ensure all scripts that interact with Neo4j (ingestion, verification, future RAG querying) consistently use the same environment variable names and loading mechanism.
