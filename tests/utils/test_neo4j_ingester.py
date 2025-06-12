"""
Unit tests for Neo4jIngester module.

These tests focus on the Neo4jIngester functionality, mocking the Neo4j Driver
to test document ingestion and database operations without requiring a real database.
"""
import os
import sys
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY

# Add project root to path to ensure imports work
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.neo4j_ingester import Neo4jIngester, DocumentIngestionData

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit

@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver with session and transaction."""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    
    # Setup mock transaction and result
    mock_result = MagicMock()
    mock_record = MagicMock()
    mock_record.__getitem__.side_effect = lambda key: {
        "id": "test_doc_001", 
        "updatedAt": "2023-01-01T00:00:00", 
        "createdAt": "2023-01-01T00:00:00"
    }.get(key)
    mock_result.single.return_value = mock_record
    mock_session.run.return_value = mock_result
    
    return mock_driver

@pytest.fixture
def sample_document_data():
    """Create a sample document for testing."""
    return DocumentIngestionData(
        doc_id="test_doc_001",
        filename="test_document.pdf",
        content="This is a test document content.",
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5],  # Short list for testing
        source_type="google_drive",
        mime_type="application/pdf",
        gdrive_id="gdrive_test_id_001",
        gdrive_webview_link="https://drive.google.com/file/d/abc123/view",
        parsed_timestamp=datetime(2023, 1, 1, 12, 0, 0),
        metadata={
            "author": "Test Author",
            "pages": 5,
            "tags": ["test", "document"],
            "importance": "high"
        }
    )


class TestNeo4jIngester:
    """Test cases for Neo4jIngester class."""

    def test_initialization(self, mock_neo4j_driver):
        """Test initialization with a valid Neo4j driver."""
        ingester = Neo4jIngester(mock_neo4j_driver)
        assert ingester.driver == mock_neo4j_driver
        
    def test_initialization_with_none_driver(self):
        """Test initialization fails with None driver."""
        with pytest.raises(ValueError, match="Neo4j Driver must be provided"):
            Neo4jIngester(None)
            
    def test_ingest_document_basic(self, mock_neo4j_driver, sample_document_data):
        """Test basic document ingestion functionality."""
        # Initialize ingester and ingest document
        ingester = Neo4jIngester(mock_neo4j_driver)
        ingester.ingest_document(sample_document_data)
        
        # Verify session.run was called and query contains expected MERGE operations
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        mock_session.run.assert_called_once()
        
        # Verify the parameters passed to the query
        args, kwargs = mock_session.run.call_args
        query = args[0]
        params = kwargs
        
        # Check that query contains MERGE operation on doc_id
        assert "MERGE (d:Document {doc_id: $doc_id})" in query
        assert params["doc_id"] == "test_doc_001"
        assert params["filename"] == "test_document.pdf"
        assert params["content"] == "This is a test document content."
        assert params["embedding"] == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert params["parsed_timestamp"] == "2023-01-01T12:00:00"

    def test_ingest_document_with_metadata(self, mock_neo4j_driver, sample_document_data):
        """Test document ingestion with metadata handling."""
        # Initialize ingester and ingest document
        ingester = Neo4jIngester(mock_neo4j_driver)
        ingester.ingest_document(sample_document_data)
        
        # Verify the parameters include metadata fields
        args, kwargs = mock_neo4j_driver.session.return_value.__enter__.return_value.run.call_args
        params = kwargs
        
        # Check metadata fields are properly extracted
        assert params["metadata_author"] == "Test Author"
        assert params["metadata_pages"] == 5
        assert params["metadata_importance"] == "high"
        # Complex types should be stringified
        assert isinstance(params["metadata_tags"], str)
        assert "test" in params["metadata_tags"]
        assert "document" in params["metadata_tags"]
        
        # Check metadata string representation
        assert "{" in params["metadata_str"]
        assert "}" in params["metadata_str"]
        
        # Check query contains metadata property assignments
        query = args[0]
        assert "d.metadata_author = $metadata_author" in query
        assert "d.metadata_pages = $metadata_pages" in query
        assert "d.metadata_tags = $metadata_tags" in query
        assert "d.metadata_importance = $metadata_importance" in query

    def test_ingest_document_database_error(self, mock_neo4j_driver, sample_document_data):
        """Test error handling during document ingestion."""
        # Setup session to raise an exception
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        mock_session.run.side_effect = Exception("Database connection error")
        
        # Initialize ingester
        ingester = Neo4jIngester(mock_neo4j_driver)
        
        # Ingestion should raise the exception
        with pytest.raises(Exception, match="Database connection error"):
            ingester.ingest_document(sample_document_data)

    def test_ingest_document_no_result(self, mock_neo4j_driver, sample_document_data):
        """Test handling when Neo4j returns no result."""
        # Setup session to return None for result.single()
        mock_result = MagicMock()
        mock_result.single.return_value = None
        mock_neo4j_driver.session.return_value.__enter__.return_value.run.return_value = mock_result
        
        # Initialize ingester
        ingester = Neo4jIngester(mock_neo4j_driver)
        
        # Should not raise but log a warning
        with patch("utils.neo4j_ingester.logger.warning") as mock_warning:
            ingester.ingest_document(sample_document_data)
            mock_warning.assert_called_once()
            assert "did not return a record" in mock_warning.call_args[0][0]

    def test_ensure_constraints_and_indices(self, mock_neo4j_driver):
        """Test creation of constraints and indices."""
        # Initialize ingester
        ingester = Neo4jIngester(mock_neo4j_driver)
        
        # Call the method
        ingester.ensure_constraints_and_indices()
        
        # Verify the session.run calls
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        assert mock_session.run.call_count == 2
        
        # Check the queries contain expected constraint and index creation statements
        first_call = mock_session.run.call_args_list[0]
        assert "CREATE CONSTRAINT" in first_call[0][0]
        assert "document_doc_id_unique" in first_call[0][0]
        
        second_call = mock_session.run.call_args_list[1]
        assert "CREATE VECTOR INDEX" in second_call[0][0]
        assert "document_embedding" in second_call[0][0]
        assert "vector.dimensions" in second_call[0][0]

    def test_ensure_constraints_error_handling(self, mock_neo4j_driver):
        """Test error handling during constraint/index creation."""
        # Setup session to raise an exception on the first call
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        mock_session.run.side_effect = [Exception("Constraint error"), None]
        
        # Initialize ingester
        ingester = Neo4jIngester(mock_neo4j_driver)
        
        # Should log error but not raise
        with patch("utils.neo4j_ingester.logger.error") as mock_error:
            ingester.ensure_constraints_and_indices()
            mock_error.assert_called_once()
            assert "Failed to ensure Neo4j constraints/indices" in mock_error.call_args[0][0]
