from typing import Optional, List
from pydantic import Field, BaseModel
# from graphiti_core.nodes import Node # No longer directly inheriting
# from graphiti_core.edges import Edge   # No longer directly inheriting

# Graphiti's Node class automatically provides 'id' and temporal fields
# (t_valid_start, t_valid_end, t_invalid_start, t_invalid_end).
# The Neo4j node label will default to the class name (e.g., "DocumentChunk").

class DocumentChunk(BaseModel):
    """
    Represents a chunk of text from a source document.
    """
    id: str
    text: str
    source_document_id: Optional[str] = None
    # We might add vector embeddings later, likely managed by LlamaIndex
    # embedding: Optional[List[float]] = Field(default=None, exclude=True) # Exclude from graph for now

    # Example of custom label if needed:
    # class Config:
    #     __label__ = "CustomChunkLabel"

class Concept(BaseModel):
    """
    Represents a concept or entity extracted from text.
    """
    id: str
    name: str = Field(..., description="The unique name of the concept.")
    description: Optional[str] = None

# Relationships
# Graphiti's Relation class requires __src__, __dst__, and __relation_type__.

class MentionsConcept(BaseModel):
    """
    Relationship from a DocumentChunk to a Concept it mentions.
    """
    # __src__ and __dst__ would typically be defined by how you add the relationship to Graphiti
    # __relation_type__ would also be defined by Graphiti or inferred
    src_id: str # Placeholder for source node ID
    dst_id: str # Placeholder for destination node ID
    relation_type: str = "MENTIONS" # Placeholder for relation type

    # Optional: Add properties to the relationship
    relevance_score: Optional[float] = None 
    # start_offset: Optional[int] = None # Example: position in text
    # end_offset: Optional[int] = None   # Example: position in text

class RelatedConcept(BaseModel):
    """
    Relationship between two Concepts.
    """
    # __src__ and __dst__ would typically be defined by how you add the relationship to Graphiti
    # __relation_type__ would also be defined by Graphiti or inferred
    src_id: str # Placeholder for source node ID
    dst_id: str # Placeholder for destination node ID
    relation_type: str = "RELATED_TO" # Placeholder for relation type

    # Optional: Describe the nature of the relationship
    relationship_description: Optional[str] = Field(default=None, description="e.g., 'is_synonym_of', 'is_part_of', 'is_broader_than'")
    strength: Optional[float] = None

# You can add more models and relationships as the project evolves.
# For example:
# class SourceDocument(Node):
#     uri: str
#     title: Optional[str] = None
#     processed_at: Optional[datetime] = None

# class HasChunk(Relation):
#     __src__ = SourceDocument
#     __dst__ = DocumentChunk
#     __relation_type__ = "HAS_CHUNK"
