from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# === UNIVERSAL ONTOLOGY FOR MULTI-DOMAIN KNOWLEDGE EXTRACTION ===
# Designed to handle: AI/Tech research, YouTube tutorials, geopolitical events,
# academic papers, business content, and diverse document types.

# --- CORE ENTITIES (Universal Building Blocks) ---

class Person(BaseModel):
    """An individual person - researchers, leaders, creators, etc."""
    person_name: str = Field(..., description="The full name of the person.")
    role: Optional[str] = Field(None, description="Their primary role or title (e.g., 'Researcher', 'President', 'YouTuber', 'CEO').")
    affiliation: Optional[str] = Field(None, description="Organization they're affiliated with.")
    expertise: Optional[List[str]] = Field(None, description="Areas of expertise or specialization.")

class Organization(BaseModel):
    """Any organized group - companies, governments, institutions, militaries."""
    organization_name: str = Field(..., description="The official name of the organization.")
    org_type: Optional[str] = Field(None, description="Type of organization (e.g., 'Company', 'Government', 'University', 'Military', 'NGO').")
    industry: Optional[str] = Field(None, description="Industry or sector the organization operates in.")
    location: Optional[str] = Field(None, description="Primary location or headquarters.")

class Location(BaseModel):
    """Geographical locations - countries, cities, regions, facilities."""
    location_name: str = Field(..., description="The name of the location.")
    location_type: Optional[str] = Field(None, description="Type of location (e.g., 'Country', 'City', 'Region', 'Facility', 'Border').")
    coordinates: Optional[str] = Field(None, description="Geographical coordinates if available.")

class Event(BaseModel):
    """Significant events - conflicts, conferences, launches, announcements."""
    event_name: str = Field(..., description="The name or description of the event.")
    event_type: Optional[str] = Field(None, description="Type of event (e.g., 'Conflict', 'Conference', 'Launch', 'Meeting', 'Attack').")
    date: Optional[str] = Field(None, description="When the event occurred or is occurring.")
    status: Optional[str] = Field(None, description="Current status (e.g., 'Ongoing', 'Completed', 'Planned').")

class Technology(BaseModel):
    """Technologies, tools, frameworks, systems - from AI models to weapons."""
    tech_name: str = Field(..., description="The name of the technology.")
    category: Optional[str] = Field(None, description="Category (e.g., 'AI Model', 'Framework', 'Weapon System', 'Platform', 'Tool').")
    version: Optional[str] = Field(None, description="Version or model number.")
    capabilities: Optional[List[str]] = Field(None, description="Key capabilities or features.")
    specifications: Optional[str] = Field(None, description="Technical specifications (e.g., '7B parameters', 'Range: 300km').")

class Content(BaseModel):
    """Any form of content - documents, videos, articles, reports."""
    content_title: str = Field(..., description="The title of the content.")
    content_type: Optional[str] = Field(None, description="Type of content (e.g., 'Video', 'Research Paper', 'News Article', 'Report', 'Tutorial').")
    platform: Optional[str] = Field(None, description="Platform where content is hosted (e.g., 'YouTube', 'arXiv', 'News Site').")
    creator: Optional[str] = Field(None, description="Creator, author, or publisher.")
    publication_date: Optional[str] = Field(None, description="When the content was published.")

class Topic(BaseModel):
    """Abstract topics, concepts, or subjects of discussion."""
    topic_name: str = Field(..., description="The name of the topic or concept.")
    domain: Optional[str] = Field(None, description="Domain this topic belongs to (e.g., 'AI', 'Geopolitics', 'Technology', 'Economics').")
    description: Optional[str] = Field(None, description="Brief description of the topic.")

class Resource(BaseModel):
    """Resources - datasets, funding, materials, territories."""
    resource_name: str = Field(..., description="The name of the resource.")
    resource_type: Optional[str] = Field(None, description="Type of resource (e.g., 'Dataset', 'Funding', 'Territory', 'Material', 'Energy').")
    quantity: Optional[str] = Field(None, description="Quantity or amount if applicable.")
    value: Optional[str] = Field(None, description="Value or importance of the resource.")

class Agreement(BaseModel):
    """Agreements, treaties, partnerships, alliances."""
    agreement_name: str = Field(..., description="The name of the agreement.")
    agreement_type: Optional[str] = Field(None, description="Type of agreement (e.g., 'Treaty', 'Alliance', 'Partnership', 'Contract').")
    parties: Optional[List[str]] = Field(None, description="Parties involved in the agreement.")
    status: Optional[str] = Field(None, description="Current status (e.g., 'Active', 'Violated', 'Expired').")

# --- List of all Node Types ---
NODES = [
    Person, Organization, Location, Event, Technology, Content, Topic, Resource, Agreement
]

# --- UNIVERSAL RELATIONSHIPS ---

class Participates(BaseModel):
    """General participation relationship - works for, fights in, speaks at, etc."""
    fact: str = Field(..., description="A concise, self-contained statement of the relationship extracted from the text.")
    valid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact became true or started. Use ISO 8601 format if providing as string input to LLM.")
    invalid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact stopped being true or ended. Use ISO 8601 format if providing as string input to LLM.")

class Located(BaseModel):
    """Location-based relationships - based in, occurs in, targets, etc."""
    fact: str = Field(..., description="A concise, self-contained statement of the relationship extracted from the text.")
    valid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact became true or started. Use ISO 8601 format if providing as string input to LLM.")
    invalid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact stopped being true or ended. Use ISO 8601 format if providing as string input to LLM.")

class Creates(BaseModel):
    """Creation relationships - develops, produces, publishes, etc."""
    fact: str = Field(..., description="A concise, self-contained statement of the relationship extracted from the text.")
    valid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact became true or started. Use ISO 8601 format if providing as string input to LLM.")
    invalid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact stopped being true or ended. Use ISO 8601 format if providing as string input to LLM.")

class Uses(BaseModel):
    """Usage relationships - employs, utilizes, deploys, etc."""
    fact: str = Field(..., description="A concise, self-contained statement of the relationship extracted from the text.")
    valid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact became true or started. Use ISO 8601 format if providing as string input to LLM.")
    invalid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact stopped being true or ended. Use ISO 8601 format if providing as string input to LLM.")

class Supports(BaseModel):
    """Support relationships - allies with, funds, backs, etc."""
    fact: str = Field(..., description="A concise, self-contained statement of the relationship extracted from the text.")
    valid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact became true or started. Use ISO 8601 format if providing as string input to LLM.")
    invalid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact stopped being true or ended. Use ISO 8601 format if providing as string input to LLM.")

class Opposes(BaseModel):
    """Opposition relationships - conflicts with, competes against, etc."""
    fact: str = Field(..., description="A concise, self-contained statement of the relationship extracted from the text.")
    valid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact became true or started. Use ISO 8601 format if providing as string input to LLM.")
    invalid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact stopped being true or ended. Use ISO 8601 format if providing as string input to LLM.")

class Discusses(BaseModel):
    """Discussion relationships - mentions, analyzes, covers, etc."""
    fact: str = Field(..., description="A concise, self-contained statement of the relationship extracted from the text.")
    valid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact became true or started. Use ISO 8601 format if providing as string input to LLM.")
    invalid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact stopped being true or ended. Use ISO 8601 format if providing as string input to LLM.")

class Controls(BaseModel):
    """Control relationships - owns, manages, governs, etc."""
    fact: str = Field(..., description="A concise, self-contained statement of the relationship extracted from the text.")
    valid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact became true or started. Use ISO 8601 format if providing as string input to LLM.")
    invalid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact stopped being true or ended. Use ISO 8601 format if providing as string input to LLM.")

class Collaborates(BaseModel):
    """Collaboration relationships - partners with, works together, etc."""
    fact: str = Field(..., description="A concise, self-contained statement of the relationship extracted from the text.")
    valid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact became true or started. Use ISO 8601 format if providing as string input to LLM.")
    invalid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact stopped being true or ended. Use ISO 8601 format if providing as string input to LLM.")

class Influences(BaseModel):
    """Influence relationships - affects, impacts, shapes, etc."""
    fact: str = Field(..., description="A concise, self-contained statement of the relationship extracted from the text.")
    valid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact became true or started. Use ISO 8601 format if providing as string input to LLM.")
    invalid_at: Optional[datetime] = Field(default=None, description="The date and time when the relationship described by the edge fact stopped being true or ended. Use ISO 8601 format if providing as string input to LLM.")

# --- List of all Relationship Types ---
RELATIONSHIPS = [
    Participates, Located, Creates, Uses, Supports, Opposes, 
    Discusses, Controls, Collaborates, Influences
]
