# Configuration models for kev-graph-rag utilities

from pathlib import Path
from typing import Optional, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GDriveReaderConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='GDRIVE_', env_file='.env', env_file_encoding='utf-8', extra='ignore')
    """Configuration for Google Drive integration."""
    credentials_path: str = Field(
        default="c:\\Users\\kevin\\repos\\kev-graph-rag\\credentials\\gdrive_service_account.json",
        description="Path to the Google service account credentials JSON file"
    )
    folder_id: Optional[str] = Field(
        default=None,
        description="The ID of the Google Drive folder to process"
    )
    impersonated_user_email: Optional[str] = Field(
        default=None,
        description="Email of the user to impersonate with domain-wide delegation (optional)"
    )
    scopes: List[str] = Field(
        default=["https://www.googleapis.com/auth/drive.readonly"],
        description="Google API scopes required for access"
    )




class LlamaParseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='LLAMAPARSE_', env_file='.env', env_file_encoding='utf-8', extra='ignore')
    """Configuration for LlamaParse integration."""
    api_key: Optional[str] = Field(
        default=None,
        description="LlamaParse API key"
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Optional custom base URL for LlamaParse API"
    )
    # Add any other LlamaParse specific settings from kev_adv_rag if needed


class ChromaDBConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='CHROMA_', env_file='.env', env_file_encoding='utf-8', extra='ignore')
    """Configuration for ChromaDB integration."""
    host: str = Field(default="localhost", description="ChromaDB server host")
    port: int = Field(default=8000, description="ChromaDB server port")
    collection_name: str = Field(
        default="documents", 
        description="Name of the collection in ChromaDB to store documents and embeddings"
    )
    auth_enabled: bool = Field(
        default=True,
        description="Whether authentication is enabled for ChromaDB"
    )
    username: Optional[str] = Field(
        default="admin",
        description="Username for ChromaDB authentication"
    )
    password: Optional[str] = Field(
        default="admin123",
        description="Password for ChromaDB authentication"
    )


class Neo4jConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='NEO4J_', env_file='.env', env_file_encoding='utf-8', extra='ignore')
    """Configuration for Neo4j integration."""
    uri: str = Field(..., description="Neo4j connection URI (e.g., 'neo4j+s://your-instance.databases.neo4j.io')")
    user: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(..., description="Neo4j password")


class EmbeddingConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='EMBEDDING_', env_file='.env', env_file_encoding='utf-8', extra='ignore')
    """Configuration for the embedding model."""
    model_name: str = Field(
        default="gemini-embedding-exp-03-07", 
        description="Name of the Gemini embedding model to use"
    )
    dimensions: int = Field(
        default=1024, 
        description="Number of dimensions for the embeddings"
    )


# Example of how these might be loaded or used in a main orchestrator config later
class IngestionOrchestratorConfig(BaseSettings):
    gdrive: GDriveReaderConfig = Field(default_factory=GDriveReaderConfig)
    llamaparse: LlamaParseConfig = Field(default_factory=LlamaParseConfig)
    chromadb: ChromaDBConfig = Field(default_factory=ChromaDBConfig)
    neo4j: Neo4jConfig = Field(default_factory=Neo4jConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    # Add other ingestion settings like target directories if we download files locally first
