from pydantic import BaseModel, Field
from typing import List, Optional

# --- Node Definitions ---
# Following Graphiti's documentation, we define custom entity types as Pydantic
# models. Graphiti will automatically handle base properties like id and name.
# We only need to define the custom attributes for each entity type.

class Organization(BaseModel):
    """An organization, such as a company, institution, or group."""
    organization_name: str = Field(..., description="The official name of the organization.")
    industry: Optional[str] = Field(None, description="The industry the organization operates in.")
    headquarters: Optional[str] = Field(None, description="The location of the organization's headquarters.")
    founded_year: Optional[int] = Field(None, description="The year the organization was founded.")

class Person(BaseModel):
    """An individual person."""
    person_name: str = Field(..., description="The full name of the person.")
    title: Optional[str] = Field(None, description="The person's job title or role.")
    skills: Optional[List[str]] = Field(None, description="A list of skills the person has.")

class Location(BaseModel):
    """A geographical location."""
    location_name: str = Field(..., description="The name of the location.")
    city: Optional[str] = Field(None, description="The city where the location is.")
    country: Optional[str] = Field(None, description="The country where the location is.")

class Event(BaseModel):
    """A specific event that occurred."""
    event_name: str = Field(..., description="The name of the event.")
    date: Optional[str] = Field(None, description="The date of the event.")
    location: Optional[str] = Field(None, description="The location where the event took place.")

class Document(BaseModel):
    """A written, printed, or electronic document."""
    title: str = Field(..., description="The title of the document.")
    author: Optional[str] = Field(None, description="The author of the document.")
    publication_date: Optional[str] = Field(None, description="The date the document was published.")

class Concept(BaseModel):
    """An abstract idea or concept."""
    concept_name: str = Field(..., description="The name of the concept.")
    domain: Optional[str] = Field(None, description="The domain or field this concept belongs to.")

class Product(BaseModel):
    """A product or service."""
    product_name: str = Field(..., description="The name of the product.")
    category: Optional[str] = Field(None, description="The category of the product.")
    manufacturer: Optional[str] = Field(None, description="The manufacturer of the product.")

class Skill(BaseModel):
    """A specific skill or capability."""
    skill_name: str = Field(..., description="The name of the skill.")
    domain: Optional[str] = Field(None, description="The domain the skill belongs to (e.g., 'Programming Language', 'Soft Skill').")

class Project(BaseModel):
    """A project or initiative."""
    project_name: str = Field(..., description="The name of the project.")
    status: Optional[str] = Field(None, description="The current status of the project (e.g., 'In Progress', 'Completed').")

class FinancialInstrument(BaseModel):
    """A financial instrument, such as a stock or bond."""
    instrument_name: str = Field(..., description="The name of the financial instrument.")
    ticker_symbol: Optional[str] = Field(None, description="The ticker symbol of the financial instrument.")
    exchange: Optional[str] = Field(None, description="The exchange where the instrument is traded.")

class Company(BaseModel):
    """A business entity."""
    company_name: str = Field(..., description="The name of the company.")
    ticker: Optional[str] = Field(None, description="The stock ticker symbol of the company.")
    industry: Optional[str] = Field(None, description="The industry the company operates in.")

class Investment(BaseModel):
    """An investment made by one entity in another."""
    investor: str = Field(..., description="The entity making the investment.")
    investee: str = Field(..., description="The entity receiving the investment.")
    amount: Optional[float] = Field(None, description="The amount of the investment.")
    date: Optional[str] = Field(None, description="The date of the investment.")

class Portfolio(BaseModel):
    """A collection of investments or assets."""
    portfolio_name: str = Field(..., description="The name of the portfolio.")
    owner: Optional[str] = Field(None, description="The owner of the portfolio.")

# --- List of all Node Types ---
NODES = [
    Organization, Person, Location, Event, Document, Concept, Product, Skill,
    Project, FinancialInstrument, Company, Investment, Portfolio
]

# --- Relationship Definitions ---
# Relationships are defined as empty Pydantic models to act as placeholders.
# Graphiti will infer the relationship properties during extraction.

class WorksFor(BaseModel):
    """Indicates that a person works for an organization."""
    pass

class LocatedIn(BaseModel):
    """Indicates that an entity is located in a specific location."""
    pass

class Manages(BaseModel):
    """Indicates that a person manages a project or organization."""
    pass

class InvestsIn(BaseModel):
    """Indicates that an entity invests in another entity."""
    pass

class Produces(BaseModel):
    """Indicates that an organization produces a product."""
    pass

class HasSkill(BaseModel):
    """Indicates that a person has a specific skill."""
    pass

class Mentions(BaseModel):
    """Indicates that a document or person mentions an entity."""
    pass

class Owns(BaseModel):
    """Indicates that an entity owns another entity or a portfolio."""
    pass

# --- List of all Relationship Types ---
RELATIONSHIPS = [
    WorksFor, LocatedIn, Manages, InvestsIn, Produces, HasSkill, Mentions, Owns
]
