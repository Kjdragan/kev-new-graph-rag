import uuid
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

class BaseNode(BaseModel):
    """
    Generic base model for a node in the knowledge graph.
    Maps to graphiti_core.EntityNode.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the node, maps to EntityNode.uuid")
    entity_name: str = Field(description="Primary name or identifier of the entity, maps to EntityNode.name")
    label: str = Field(description="Primary type/label of the node, used to populate EntityNode.labels (e.g., labels=[label])")
    description: Optional[str] = Field(default=None, description="Brief description of the entity")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Custom properties for the node, maps to EntityNode.attributes")
    confidence_score: float = Field(default=1.0, description="Confidence score for this entity extraction (0.0-1.0)")
    aliases: Optional[List[str]] = Field(default=None, description="Alternative names or identifiers for this entity")

    class Config:
        frozen = True # Pydantic v2 style for hashable models if needed later

class Entity(BaseNode):
    """Generic entity type for when a more specific type is not applicable."""
    label: str = Field(default="Entity", description="Label for a generic entity.")

class Person(BaseNode):
    """Person entity representing an individual."""
    label: str = Field(default="Person", description="Label for a person entity.")
    full_name: Optional[str] = Field(default=None, description="Full name of the person")
    role: Optional[str] = Field(default=None, description="Professional role or title")
    organization: Optional[str] = Field(default=None, description="Organization the person is affiliated with")

class Organization(BaseNode):
    """Organization entity representing a company, institution, or formal group."""
    label: str = Field(default="Organization", description="Label for an organization entity.")
    founded_year: Optional[int] = Field(default=None, description="Year the organization was founded")
    industry: Optional[str] = Field(default=None, description="Industry the organization operates in")
    headquarters: Optional[str] = Field(default=None, description="Location of headquarters")

class Location(BaseNode):
    """Location entity representing a geographic place."""
    label: str = Field(default="Location", description="Label for a location entity.")
    country: Optional[str] = Field(default=None, description="Country name")
    city: Optional[str] = Field(default=None, description="City name")
    address: Optional[str] = Field(default=None, description="Street address")
    coordinates: Optional[str] = Field(default=None, description="Geographic coordinates")

class Concept(BaseNode):
    """Concept entity representing an abstract idea, theory, or theme."""
    label: str = Field(default="Concept", description="Label for a concept entity.")
    domain: Optional[str] = Field(default=None, description="Domain or field this concept belongs to")
    related_terms: Optional[List[str]] = Field(default=None, description="Related terms or concepts")

class Product(BaseNode):
    """Product entity representing a good, service, or offering."""
    label: str = Field(default="Product", description="Label for a product entity.")
    category: Optional[str] = Field(default=None, description="Product category")
    manufacturer: Optional[str] = Field(default=None, description="Product manufacturer")
    features: Optional[List[str]] = Field(default=None, description="Key features of the product")

class Event(BaseNode):
    """Event entity representing a time-bound occurrence."""
    label: str = Field(default="Event", description="Label for an event entity.")
    date: Optional[str] = Field(default=None, description="Date of the event")
    location: Optional[str] = Field(default=None, description="Location of the event")
    participants: Optional[List[str]] = Field(default=None, description="Participants in the event")

class Document(BaseNode):
    """Document entity representing a text document or file."""
    label: str = Field(default="Document", description="Label for a document node.")
    source_url: Optional[str] = Field(default=None, description="URL or path of the source document")
    content_hash: Optional[str] = Field(default=None, description="Hash of the document content")
    author: Optional[str] = Field(default=None, description="Author of the document")
    publication_date: Optional[str] = Field(default=None, description="Publication date of the document")

# Export all node types
NODES = [
    Entity, 
    Person, 
    Organization, 
    Location, 
    Concept, 
    Product, 
    Event, 
    Document
]

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
    confidence_score: float = Field(default=1.0, description="Confidence score for this relationship extraction (0.0-1.0)")
    source_context: Optional[str] = Field(default=None, description="Text snippet from source supporting this relationship")

    class Config:
        frozen = True

class RelatesTo(BaseRelationship):
    """Generic relationship type for when a more specific type is not applicable."""
    type: str = Field(default="RELATES_TO", description="Generic relationship type.")

class WorksFor(BaseRelationship):
    """Relationship indicating employment or affiliation."""
    type: str = Field(default="WORKS_FOR", description="Employment or affiliation relationship.")
    role: Optional[str] = Field(default=None, description="Role in the organization")
    start_date: Optional[str] = Field(default=None, description="Start date of employment")
    end_date: Optional[str] = Field(default=None, description="End date of employment, if applicable")

class LocatedIn(BaseRelationship):
    """Relationship indicating physical location."""
    type: str = Field(default="LOCATED_IN", description="Physical location relationship.")
    address_type: Optional[str] = Field(default=None, description="Type of location (e.g., headquarters, branch)")

class Creates(BaseRelationship):
    """Relationship indicating creation or authorship."""
    type: str = Field(default="CREATES", description="Creation or authorship relationship.")
    creation_date: Optional[str] = Field(default=None, description="Date of creation")

class PartOf(BaseRelationship):
    """Relationship indicating component or membership."""
    type: str = Field(default="PART_OF", description="Component or membership relationship.")
    role: Optional[str] = Field(default=None, description="Role within the larger entity")

class Mentions(BaseRelationship):
    """Relationship indicating reference or mention."""
    type: str = Field(default="MENTIONS", description="Reference or mention relationship.")
    context: Optional[str] = Field(default=None, description="Context of the mention")
    sentiment: Optional[str] = Field(default=None, description="Sentiment of the mention (positive, negative, neutral)")

class Owns(BaseRelationship):
    """Relationship indicating ownership."""
    type: str = Field(default="OWNS", description="Ownership relationship.")
    ownership_percentage: Optional[str] = Field(default=None, description="Percentage of ownership, if applicable")
    acquisition_date: Optional[str] = Field(default=None, description="Date of acquisition")

class Uses(BaseRelationship):
    """Relationship indicating usage or utilization."""
    type: str = Field(default="USES", description="Usage or utilization relationship.")
    purpose: Optional[str] = Field(default=None, description="Purpose of usage")

# Export all relationship types
RELATIONSHIPS = [
    RelatesTo,
    WorksFor,
    LocatedIn,
    Creates,
    PartOf,
    Mentions,
    Owns,
    Uses
]
