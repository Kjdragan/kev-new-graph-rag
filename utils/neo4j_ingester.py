# Neo4j Ingester for kev-graph-rag

from typing import List, Dict, Any, Optional
from datetime import datetime

from neo4j import Driver
from pydantic import BaseModel, Field
from loguru import logger


class DocumentIngestionData(BaseModel):
    """Model for data to be ingested into Neo4j as a :Document node."""
    doc_id: str = Field(description="Unique identifier for the document, e.g., Google Drive file ID")
    filename: str = Field(description="Original filename of the document")
    content: str = Field(description="Parsed text content of the document")
    embedding: List[float] = Field(description="Vector embedding of the document content")
    source_type: str = Field(default="google_drive", description="Source of the document, e.g., 'google_drive'")
    mime_type: Optional[str] = Field(default=None, description="MIME type of the original file")
    gdrive_id: Optional[str] = Field(default=None, description="Google Drive specific file ID, if applicable")
    gdrive_webview_link: Optional[str] = Field(default=None, description="Google Drive web view link, if applicable")
    parsed_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the document was parsed and processed")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Other arbitrary metadata")


class Neo4jIngester:
    """Handles ingestion of document data into Neo4j."""

    def __init__(self, driver: Driver):
        """Initialize the Neo4j Ingester.

        Args:
            driver: Neo4j Python driver instance.
        """
        if not driver:
            raise ValueError("Neo4j Driver must be provided.")
        self.driver = driver

    def ingest_document(self, doc_data: DocumentIngestionData) -> None:
        """Ingests a single document into Neo4j as a :Document node.

        Uses MERGE to ensure idempotency based on doc_id.

        Args:
            doc_data: The document data to ingest.
        """
        query = (
            "MERGE (d:Document {doc_id: $doc_id}) "
            "ON CREATE SET "
            "  d.filename = $filename, "
            "  d.content = $content, "
            "  d.embedding = $embedding, "
            "  d.source_type = $source_type, "
            "  d.mime_type = $mime_type, "
            "  d.gdrive_id = $gdrive_id, "
            "  d.gdrive_webview_link = $gdrive_webview_link, "
            "  d.parsed_timestamp = datetime($parsed_timestamp), "
            "  d.metadata = $metadata, "
            "  d.created_at = datetime() "
            "ON MATCH SET "
            "  d.filename = $filename, "
            "  d.content = $content, "
            "  d.embedding = $embedding, "
            "  d.mime_type = $mime_type, "
            "  d.gdrive_webview_link = $gdrive_webview_link, "
            "  d.parsed_timestamp = datetime($parsed_timestamp), "
            "  d.metadata = $metadata, "
            "  d.updated_at = datetime() "
            "RETURN d.doc_id AS id, d.updated_at AS updatedAt, d.created_at AS createdAt"
        )

        params = {
            "doc_id": doc_data.doc_id,
            "filename": doc_data.filename,
            "content": doc_data.content,
            "embedding": doc_data.embedding,
            "source_type": doc_data.source_type,
            "mime_type": doc_data.mime_type,
            "gdrive_id": doc_data.gdrive_id or doc_data.doc_id, # Use doc_id if gdrive_id not explicitly set
            "gdrive_webview_link": doc_data.gdrive_webview_link,
            "parsed_timestamp": doc_data.parsed_timestamp.isoformat(),
            "metadata": doc_data.metadata
        }

        try:
            with self.driver.session() as session:
                result = session.run(query, params)
                record = result.single()
                if record:
                    action = "updated" if record["updatedAt"] else "created"
                    logger.info(f"Successfully {action} :Document node with doc_id '{record['id']}' in Neo4j.")
                else:
                    logger.warning(f"Neo4j MERGE for doc_id '{doc_data.doc_id}' did not return a record.")
        except Exception as e:
            logger.error(f"Failed to ingest document with doc_id '{doc_data.doc_id}' into Neo4j: {e}")
            raise

    def ensure_constraints_and_indices(self) -> None:
        """Ensures necessary constraints and indices for :Document nodes exist."""
        queries = [
            "CREATE CONSTRAINT document_doc_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.doc_id IS UNIQUE",
            "CREATE VECTOR INDEX document_embedding IF NOT EXISTS FOR (d:Document) ON (d.embedding) OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}}" # Adjust dimensions as per your Gemini model
        ]
        # Note: Gemini embedding model 'gemini-embedding-exp-03-07' (if that's what you're using) has 1024 dimensions.
        # The 'embedding-001' model for google-genai has 768 dimensions.
        # Please verify and adjust `vector.dimensions` accordingly.

        try:
            with self.driver.session() as session:
                for i, query in enumerate(queries):
                    logger.info(f"Running setup query [{i+1}/{len(queries)}]: {query.split(' IF NOT EXISTS')[0]}...")
                    session.run(query)
                logger.info("Successfully ensured Neo4j constraints and vector index for :Document nodes.")
        except Exception as e:
            logger.error(f"Failed to ensure Neo4j constraints/indices: {e}")
            # Decide if this should raise or just warn

# Example Usage (for testing purposes)
if __name__ == '__main__':
    # This example requires a running Neo4j instance and credentials in .env
    # and the neo4j Python driver installed.
    from dotenv import load_dotenv
    import os

    project_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(dotenv_path=project_root / '.env')

    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("SKIPPING Neo4jIngester example: Neo4j credentials not found in .env")
    else:
        try:
            driver = Driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            ingester = Neo4jIngester(driver)
            
            # Ensure constraints and indices are set up (idempotent)
            ingester.ensure_constraints_and_indices()
            print("Checked/Ensured Neo4j constraints and indices.")

            # Create dummy data for ingestion
            dummy_doc = DocumentIngestionData(
                doc_id="test_doc_001",
                filename="test_document.txt",
                content="This is a test document for Neo4j ingestion.",
                embedding=[0.1] * 1024, # Replace 1024 with your actual embedding dimension
                gdrive_id="test_doc_001_gdrive",
                metadata={"category": "test", "version": 1}
            )
            
            print(f"Ingesting dummy document: {dummy_doc.doc_id}")
            ingester.ingest_document(dummy_doc)
            print(f"Dummy document {dummy_doc.doc_id} ingestion attempt complete.")

            # You can verify in Neo4j Browser: MATCH (d:Document {doc_id: 'test_doc_001'}) RETURN d

        except Exception as e:
            print(f"Error during Neo4jIngester example: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if 'driver' in locals() and driver:
                driver.close()
                print("Neo4j driver closed.")
