# src/ontology_templates/financial_report_ontology.py
from typing import List, Optional
from pydantic import Field
from .generic_ontology import BaseNode, BaseRelationship

# --- Entity Types (Nodes) ---

class Company(BaseNode):
    label: str = Field(default="Company")
    stock_symbol: Optional[str] = Field(default=None, description="Stock symbol of the company")
    industry: Optional[str] = Field(default=None, description="Industry the company operates in")

class Person(BaseNode):
    label: str = Field(default="Person")
    role: Optional[str] = Field(default=None, description="Role of the person (e.g., CEO, Analyst)")

class FinancialMetric(BaseNode):
    label: str = Field(default="FinancialMetric")
    value: Optional[str] = Field(default=None, description="Value of the financial metric (e.g., '$10M', '5%')")
    period: Optional[str] = Field(default=None, description="Time period the metric refers to (e.g., 'Q4 2023')")

class ProductService(BaseNode):
    label: str = Field(default="ProductService")
    category: Optional[str] = Field(default=None, description="Category of the product or service")

class Location(BaseNode):
    label: str = Field(default="Location")
    address: Optional[str] = Field(default=None, description="Address of the location")
    city: Optional[str] = Field(default=None)
    country: Optional[str] = Field(default=None)

class ReportSection(BaseNode):
    label: str = Field(default="ReportSection")
    section_title: str = Field(description="Title of the report section")
    summary: Optional[str] = Field(default=None, description="Optional summary of the section")

class KeyFinding(BaseNode):
    label: str = Field(default="KeyFinding")
    finding_text: str = Field(description="Text of the key finding")
    sentiment: Optional[str] = Field(default=None, description="Sentiment of the finding (e.g., positive, negative, neutral)")


# --- Relationship Types (Edges) ---

class ReportsTo(BaseRelationship):
    type: str = Field(default="REPORTS_TO")

class WorksAt(BaseRelationship):
    type: str = Field(default="WORKS_AT")
    role: Optional[str] = Field(default=None, description="Role associated with the employment")

class HasFinancialMetric(BaseRelationship):
    type: str = Field(default="HAS_FINANCIAL_METRIC")
    metric_type: str = Field(description="Type of financial metric (e.g., 'Revenue', 'Net Income')")

class MentionsMetric(BaseRelationship):
    type: str = Field(default="MENTIONS_METRIC")
    sentiment: Optional[str] = Field(default=None, description="Sentiment of the mention (e.g., 'positive', 'negative')")

class OffersProductService(BaseRelationship):
    type: str = Field(default="OFFERS_PRODUCT_SERVICE")

class LocatedIn(BaseRelationship):
    type: str = Field(default="LOCATED_IN")

class IsPeerOf(BaseRelationship):
    type: str = Field(default="IS_PEER_OF")
    reason: Optional[str] = Field(default=None, description="Reason for being considered a peer")

class HasSubsidiary(BaseRelationship):
    type: str = Field(default="HAS_SUBSIDIARY")

class DISCUSSES_METRIC(BaseRelationship):
    type: str = Field(default="DISCUSSES_METRIC")
    context: Optional[str] = Field(default=None, description="Specific context of the metric discussion")

class HAS_FINDING(BaseRelationship):
    type: str = Field(default="HAS_FINDING")

class MENTIONS_COMPANY(BaseRelationship):
    type: str = Field(default="MENTIONS_COMPANY")
    context: Optional[str] = Field(default=None, description="Specific context of the company mention")


# List of all node types for the ontology
NODES = [Company, Person, FinancialMetric, ProductService, Location, ReportSection, KeyFinding]
# List of all relationship types for the ontology
RELATIONSHIPS = [ReportsTo, WorksAt, HasFinancialMetric, MentionsMetric, OffersProductService, LocatedIn, IsPeerOf, HasSubsidiary, DISCUSSES_METRIC, HAS_FINDING, MENTIONS_COMPANY]
