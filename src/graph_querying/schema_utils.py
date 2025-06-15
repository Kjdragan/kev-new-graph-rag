"""
Utilities for extracting and formatting the Pydantic ontology schema 
for use in LLM prompts.
"""
import inspect
from typing import Any, Dict, List, Optional, Type, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo

# Attempt to import NODES and RELATIONSHIPS from the project's ontology
try:
    from src.ontology_templates.universal_ontology import NODES, RELATIONSHIPS
except ImportError:
    # This allows the module to be imported in environments where the full project structure isn't available,
    # e.g., for unit testing components in isolation, though get_ontology_schema_string will fail.
    NODES = []
    RELATIONSHIPS = [] 

def _get_field_type_str(field_info: FieldInfo) -> str:
    """Helper function to get a string representation of a Pydantic field's type."""
    field_type = field_info.annotation
    origin = get_origin(field_type)
    args = get_args(field_type)

    if origin:
        if args:
            arg_names = [arg.__name__ if hasattr(arg, '__name__') else str(arg) for arg in args]
            # Handle Optional[datetime] specifically for clarity
            if origin is Optional and any(a == 'datetime' for a in arg_names):
                return "Optional[datetime]"
            return f"{origin.__name__}[{', '.join(arg_names)}]"
        return origin.__name__
    return field_type.__name__ if hasattr(field_type, '__name__') else str(field_type)

def get_ontology_schema_string(
    node_types: Optional[List[Type[BaseModel]]] = None,
    relationship_types: Optional[List[Type[BaseModel]]] = None,
    edge_type_map: Optional[Dict[tuple[str, str], List[str]]] = None
) -> str:
    """
    Generates a markdown string describing the ontology schema from Pydantic models.

    Args:
        node_types: A list of Pydantic BaseModel classes representing node types.
                    Defaults to NODES from universal_ontology.py.
        relationship_types: A list of Pydantic BaseModel classes representing relationship types.
                            Defaults to RELATIONSHIPS from universal_ontology.py.
        edge_type_map: A dictionary defining valid connections between node types,
                       e.g., {('Person', 'Organization'): ['WORKS_FOR']}.

    Returns:
        A markdown string describing the ontology schema.
    """
    if node_types is None:
        node_types = NODES
    if relationship_types is None:
        relationship_types = RELATIONSHIPS

    if not NODES or not RELATIONSHIPS:
        if not node_types or not relationship_types:
            return ("ERROR: Ontology models (NODES and/or RELATIONSHIPS) not found or not provided. "
                    "Ensure src.ontology_templates.universal_ontology.py is accessible and defines them.")

    schema_parts = []

    schema_parts.append("## Ontology Schema for Cypher Query Generation")
    schema_parts.append(
        "This schema defines the structure of the knowledge graph. "
        "Use it to construct Cypher queries. Pay close attention to property names, types, "
        "and relationship directions."
    )

    schema_parts.append("\n### Node Types:")
    for node_model in node_types:
        schema_parts.append(f"\n#### Node: `{node_model.__name__}`")
        if node_model.__doc__:
            schema_parts.append(f"Description: {node_model.__doc__.strip()}")
        schema_parts.append("Properties:")
        for name, field_info in node_model.model_fields.items():
            type_str = _get_field_type_str(field_info)
            description = field_info.description or "No description."
            schema_parts.append(f"  - `{name}` ({type_str}): {description}")

    schema_parts.append("\n### Relationship Types:")
    for rel_model in relationship_types:
        schema_parts.append(f"\n#### Relationship: `{rel_model.__name__}`")
        if rel_model.__doc__:
            schema_parts.append(f"Description: {rel_model.__doc__.strip()}")
        schema_parts.append("Properties:")
        for name, field_info in rel_model.model_fields.items():
            type_str = _get_field_type_str(field_info)
            description = field_info.description or "No description."
            schema_parts.append(f"  - `{name}` ({type_str}): {description}")
            if name in ["valid_at", "invalid_at"]:
                schema_parts.append(
                    f"    *Note: For `{name}`, use the `$current_datetime` parameter in Cypher queries "
                    f"for temporal filtering (e.g., `r.{name} <= $current_datetime`).*"
                )

    if edge_type_map:
        schema_parts.append("\n### Allowed Relationship Structures:")
        schema_parts.append("Format: `(SourceNodeType)-[RelationshipType]->(TargetNodeType)`")
        for (source_node_name, target_node_name), rel_names in edge_type_map.items():
            for rel_name in rel_names:
                schema_parts.append(f"- `({source_node_name})-[{rel_name}]->({target_node_name})`")
    else:
        schema_parts.append(
            "\n*Note: Specific (Source)-[Relationship]->(Target) structures are not detailed here. "
            "The LLM should infer valid connections based on relationship and node type descriptions, "
            "or a more detailed edge_type_map can be provided if needed.*"
        )
    
    schema_parts.append("\n### Temporal Querying Notes:")
    schema_parts.append(
        "- When filtering by time, always use the `$current_datetime` parameter which will be provided at runtime."
    )
    schema_parts.append(
        "- For active relationships at the current time, typical conditions are: "
        "`r.valid_at <= $current_datetime AND (r.invalid_at IS NULL OR r.invalid_at > $current_datetime)`."
    )
    schema_parts.append(
        "- For relationships valid at a *specific past or future time* (if the query implies it), "
        "that specific time should be used instead of `$current_datetime` for the relevant bounds."
    )

    return "\n".join(schema_parts)

if __name__ == '__main__':
    # Example usage (assuming universal_ontology.py is in the python path):
    print("Generating schema string from default ontology...")
    schema_str = get_ontology_schema_string()
    print(schema_str)

    # Example with a dummy edge_type_map
    dummy_edge_map = {
        ('Person', 'Organization'): ['WORKS_FOR', 'ADVISES'],
        ('Organization', 'Technology'): ['DEVELOPS'],
        ('Content', 'Topic'): ['DISCUSSES']
    }
    print("\n\nGenerating schema string with a dummy edge_type_map...")
    schema_str_with_map = get_ontology_schema_string(edge_type_map=dummy_edge_map)
    print(schema_str_with_map)
