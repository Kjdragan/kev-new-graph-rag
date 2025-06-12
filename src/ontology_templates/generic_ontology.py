import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class BaseNode(BaseModel):
    """
    Generic base model for a node in the knowledge graph.
    Maps to graphiti_core.EntityNode.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the node, maps to EntityNode.uuid")
    name: str = Field(description="Primary name or identifier of the entity, maps to EntityNode.name")
    label: str = Field(description="Primary type/label of the node, used to populate EntityNode.labels (e.g., labels=[label])")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Custom properties for the node, maps to EntityNode.attributes")

    class Config:
        frozen = True # Pydantic v2 style for hashable models if needed later

class Entity(BaseNode):
    label: str = Field(default="Entity", description="Label for a generic entity.")

class Document(BaseNode):
    label: str = Field(default="Document", description="Label for a document node.")
    source_url: Optional[str] = Field(default=None, description="URL or path of the source document.")
    content_hash: Optional[str] = Field(default=None, description="Hash of the document content.")


NODES = [Entity, Document]


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
    properties: Dict[str, Any] = Field(default_factory=dict, description="Custom properties for the relationship, maps to EntityEdge.attributes")

    class Config:
        frozen = True


class RelatesTo(BaseRelationship):
    type: str = Field(default="RELATES_TO", description="Generic relationship type.")


RELATIONSHIPS = [RelatesTo]
