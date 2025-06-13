# Report: Ensuring Correct Data Types for Neo4j Properties in Graphiti Extractions

Date: 2025-06-13

## 1. Executive Summary

This report addresses the challenge of ensuring that data extracted by Graphiti and ingested into Neo4j adheres to Neo4j's property type constraints. Neo4j requires all node and relationship properties to be primitive types (e.g., string, integer, float, boolean) or lists of these primitive types. Complex nested objects or dictionaries are not directly supported as property values.

The investigation revealed that while node attributes are likely well-typed due to Graphiti's use of `entity_types` during episode ingestion, relationship attributes are more prone to containing complex, non-primitive values. This is because Graphiti's `add_episode` method does not have a direct mechanism to enforce a Pydantic-defined structure for relationship attributes in the same way it does for node attributes.

This report proposes a two-phased approach:
1.  **Phase 1 (Definition & Guidance):** Strengthen the Pydantic model definitions for relationship attributes in the project's ontology to provide clearer guidance and enforce stricter typing within the Python codebase.
2.  **Phase 2 (Post-Processing - If Necessary):** Implement explicit post-processing logic within the `GraphExtractor` to iterate through extracted relationship attributes and ensure they are flattened or converted to Neo4j-compatible types before final ingestion.

## 2. Problem Statement

The core issue is that the `kev-new-graph-rag` project has been encountering extractions where knowledge graph relationships have property values that are not primitive types or arrays of primitive types. This is incompatible with Neo4j's storage requirements and can lead to ingestion failures or incorrectly stored data.

## 3. Analysis of Current Implementation

-   **Ingestion Script (`ingest_gdrive_documents.py`):** This script orchestrates the document processing pipeline, utilizing a `GraphExtractor` class.
-   **Graph Extractor (`src/graph_extraction/extractor.py`):**
    -   This class is responsible for interacting with the `graphiti-core` library.
    -   It uses the `graphiti_instance.add_episode()` method for ingesting data from text content.
    -   Importantly, it correctly uses `add_episode` and **not** `add_episode_bulk`. This is crucial as `add_episode` supports edge invalidation (updating existing relationships based on new information), which is generally desirable for evolving knowledge graphs.
-   **Ontology Definitions (`src/ontology_templates/generic_ontology.py`):
    -   **Node Attributes:** Node types (e.g., `Person`, `Organization`) inherit from `BaseNode`. The `BaseNode.properties` field is well-defined with a type hint `Dict[str, Union[str, int, float, bool, List[str], List[int], List[float], List[bool]]]` and a clear description emphasizing the use of Neo4j-compatible primitive types. When `graphiti.add_episode()` is called with `entity_types` (populated by these node Pydantic models), Graphiti's LLM is guided to extract node attributes according to these definitions, making node properties less likely to have type issues.
    -   **Relationship Attributes:** Relationship types (e.g., `WorksFor`, `LocatedIn`) inherit from `BaseRelationship`. The primary concern lies here. Graphiti's `add_episode` method does not accept a `relationship_types` parameter analogous to `entity_types`. Therefore, the structure and typing of relationship attributes are determined more by the LLM's general interpretation during the extraction process. Graphiti's internal `EntityEdge` model (which represents extracted relationships) has an `attributes: Dict[str, Any]` field. If the LLM populates this dictionary with complex objects (e.g., nested Pydantic models or dictionaries) instead of simple primitive values, these are passed to Neo4j, leading to the observed type errors.
    -   The `BaseRelationship.properties` field in the current ontology was typed as `Dict[str, Any]`, offering less guidance than its `BaseNode` counterpart.

## 4. Proposed Solutions

### Phase 1: Strengthen Ontology Definitions for Relationships

The first and most immediate step is to make the Pydantic definition for relationship attributes as strict and explicit as it is for node attributes. This provides better guidance for any part of the system (including potential indirect influence on the LLM or direct use of these models in Python code) and improves code robustness.

**Concrete Change:**

Modify the `BaseRelationship` class in `src/ontology_templates/generic_ontology.py` as follows:

**File:** `c:\Users\kevin\repos\kev-new-graph-rag\src\ontology_templates\generic_ontology.py`

```python
# ... (other imports and code) ...

class BaseRelationship(BaseModel):
    """
    Generic base model for a relationship in the knowledge graph.
    Maps to graphiti_core.EntityEdge.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the relationship, maps to EntityEdge.uuid")
    source_id: str = Field(description="Identifier of the source node, maps to EntityEdge.source_node_uuid")
    target_id: str = Field(description="Identifier of the target node, maps to EntityEdge.target_node_uuid")
    type: str = Field(description="Type of the relationship, maps to EntityEdge.name")
    fact: str = Field(description="Textual description of the relationship/fact, maps to EntityEdge.fact")
    # MODIFIED SECTION START
    properties: Dict[str, Union[str, int, float, bool, List[str], List[int], List[float], List[bool]]] = Field(
        default_factory=dict, 
        description="Custom properties for the relationship. All values MUST be Neo4j-compatible primitive types (str, int, float, bool) or lists of these primitives. Complex objects or nested structures are NOT allowed here and should be modeled as separate nodes and relationships."
    )
    # MODIFIED SECTION END
    confidence_score: float = Field(default=1.0, description="Confidence score for this relationship extraction (0.0-1.0)")
    source_context: Optional[str] = Field(default=None, description="Text snippet from source supporting this relationship")

    class Config:
        frozen = True

# ... (rest of the file) ...
```

**Rationale for Phase 1:**
-   Aligns relationship attribute definitions with best practices already implemented for node attributes.
-   Provides clearer intent and stricter typing within the Python codebase.
-   May offer some indirect guidance to Graphiti's internal LLM during extraction.

### Phase 2: Implement Post-Processing in `GraphExtractor` (If Necessary)

If modifying the ontology (Phase 1) does not fully resolve the issue of complex relationship attributes, a more direct approach is to implement post-processing logic within the `GraphExtractor.extract` method.

**Conceptual Steps for Post-Processing:**

1.  **After Extraction:** Once `add_episode_result = await self.graphiti_instance.add_episode(...)` is called and results are returned.
2.  **Iterate Edges:** Loop through each `edge` in `add_episode_result.edges`.
3.  **Inspect Attributes:** For each `edge.attributes` dictionary:
    *   Check each value to ensure it is a Neo4j-compatible primitive type or a list of such primitives.
    *   If a value is a complex object (e.g., a nested dictionary, a Pydantic model instance), implement logic to flatten it or convert it appropriately. For example:
        *   A nested dictionary `{'detail': {'type': 'A', 'value': 1}}` might be flattened to `{'detail_type': 'A', 'detail_value': 1}`.
        *   A Pydantic model instance could be converted to its dictionary representation (`model.model_dump()`) and then flattened if necessary.
4.  **Update Edge Attributes:** Replace the original `edge.attributes` with the processed, flattened dictionary.
5.  **Return Processed Results:** The `GraphExtractor.extract` method would then return these cleaned `extraction_results`.

**Rationale for Phase 2:**
-   Provides direct control over the final structure of relationship attributes before they are used for Neo4j ingestion.
-   Acts as a safeguard to ensure Neo4j compatibility regardless of the LLM's raw extraction output for relationship properties.

## 5. Conclusion and Next Steps

It is recommended to first implement Phase 1 (strengthening the `BaseRelationship` Pydantic model). After applying this change and re-testing the ingestion pipeline, if issues with complex relationship property types persist, then proceed to implement Phase 2 (post-processing logic in `GraphExtractor`).

This structured approach aims to resolve the property type incompatibility with Neo4j, leading to a more robust and reliable data ingestion pipeline.
