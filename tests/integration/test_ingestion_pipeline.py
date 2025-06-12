"""
Integration tests for document ingestion pipeline.

These tests focus on the flow from document parsing through embedding to storage,
testing the interaction between components with external APIs mocked.
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

from utils.document_parser import DocumentParser
from utils.embedding import CustomGeminiEmbedding
from utils.chroma_ingester import ChromaIngester
from utils.neo4j_ingester import Neo4jIngester, DocumentIngestionData
from utils.config_models import LlamaParseConfig, ChromaDBConfig

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

@pytest.fixture
def mock_llama_parser():
    """Mock LlamaParse client."""
    with patch("utils.document_parser.LlamaParse") as mock_parser_class:
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        
        # Setup mock parse response
        mock_response = [
            {"text": "Sample document content page 1.", "page_or_section_index": 0, "metadata": {"page": 1}},
            {"text": "Sample document content page 2.", "page_or_section_index": 1, "metadata": {"page": 2}}
        ]
        mock_parser.parse_document.return_value = mock_response
        
        yield mock_parser

@pytest.fixture
def mock_embedding_client():
    """Mock the Gemini embedding client."""
    with patch("utils.embedding.genai.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock embeddings response
        mock_embeddings = [0.1, 0.2, 0.3, 0.4, 0.5] * 100  # 500-dim vector
        mock_response = {"embeddings": [mock_embeddings]}
        mock_client.models.embed_content.return_value = mock_response
        
        yield mock_client

@pytest.fixture
def mock_chromadb_client():
    """Mock ChromaDB client."""
    with patch("utils.chroma_ingester.chromadb.HttpClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock collection
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        
        yield mock_client

@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver."""
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
def sample_document_path(tmp_path):
    """Create a sample document file for testing."""
    doc_path = tmp_path / "test_document.txt"
    with open(doc_path, 'w') as f:
        f.write("This is a test document.\nIt has multiple lines of content.")
    return doc_path


class TestDocumentProcessingPipeline:
    """Integration tests for the full document processing pipeline."""

    def test_end_to_end_document_processing(
        self, 
        sample_document_path, 
        mock_llama_parser, 
        mock_embedding_client, 
        mock_chromadb_client, 
        mock_neo4j_driver, 
        monkeypatch
    ):
        """Test the full pipeline from document parsing to storage."""
        # Set environment variable for API key
        monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key")
        
        # Initialize components
        parser_config = LlamaParseConfig(api_key="test-llama-api-key")
        parser = DocumentParser(config=parser_config)
        
        embedding_model = CustomGeminiEmbedding(
            google_api_key="test-api-key",
            model_name="gemini-embedding-test-model"
        )
        
        chroma_config = ChromaDBConfig(
            host="localhost",
            port=8000,
            collection_name="test_collection"
        )
        chroma_ingester = ChromaIngester(config=chroma_config)
        
        neo4j_ingester = Neo4jIngester(mock_neo4j_driver)
        
        # Process document: Parse -> Embed -> Store
        
        # 1. Parse document
        parsed_content = parser.parse_file(sample_document_path)
        assert len(parsed_content) == 2
        
        # Extract concatenated text for embedding
        concatenated_text = " ".join([item["text"] for item in parsed_content])
        
        # 2. Generate embedding
        embedding = embedding_model._get_text_embedding(concatenated_text)
        assert len(embedding) > 0
        
        # Check that the embedding API was called with the right parameters
        mock_embedding_client.models.embed_content.assert_called_once()
        args, kwargs = mock_embedding_client.models.embed_content.call_args
        assert "Sample document content page" in kwargs["contents"]
        assert kwargs["model"] == "gemini-embedding-test-model"
        
        # 3. Ingest to ChromaDB
        doc_id = "test_doc_001"
        metadata = {
            "filename": sample_document_path.name,
            "source": "test",
            "mime_type": "text/plain"
        }
        
        chroma_ingester.ingest_document(
            doc_id=doc_id, 
            content=concatenated_text, 
            embedding=embedding, 
            metadata=metadata
        )
        
        # Check that ChromaDB collection was created and document added
        mock_chromadb_client.get_or_create_collection.assert_called_once_with(
            name="test_collection",
            metadata=ANY
        )
        
        # Get the mock collection and check upsert was called
        mock_collection = mock_chromadb_client.get_or_create_collection.return_value
        mock_collection.upsert.assert_called_once()
        
        # 4. Ingest to Neo4j
        document_data = DocumentIngestionData(
            doc_id=doc_id,
            filename=sample_document_path.name,
            content=concatenated_text,
            embedding=embedding,
            source_type="test",
            mime_type="text/plain",
            parsed_timestamp=datetime.now(),
            metadata=metadata
        )
        
        neo4j_ingester.ingest_document(document_data)
        
        # Check that Neo4j session.run was called
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        mock_session.run.assert_called_once()
        
        # Get the query and params used for Neo4j
        args, kwargs = mock_session.run.call_args
        query = args[0]
        params = kwargs
        
        # Check that query contains MERGE operation
        assert "MERGE (d:Document {doc_id: $doc_id})" in query
        assert params["doc_id"] == "test_doc_001"
        assert "Sample document content" in params["content"]

    def test_error_recovery_between_components(
        self, 
        sample_document_path, 
        mock_llama_parser, 
        mock_embedding_client, 
        mock_chromadb_client, 
        mock_neo4j_driver, 
        monkeypatch
    ):
        """Test error recovery and retries between pipeline components."""
        # Set environment variable for API key
        monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key")
        
        # Initialize components
        parser_config = LlamaParseConfig(api_key="test-llama-api-key")
        parser = DocumentParser(config=parser_config)
        
        embedding_model = CustomGeminiEmbedding(
            google_api_key="test-api-key",
            model_name="gemini-embedding-test-model"
        )
        
        chroma_config = ChromaDBConfig(
            host="localhost",
            port=8000,
            collection_name="test_collection"
        )
        chroma_ingester = ChromaIngester(config=chroma_config)
        
        neo4j_ingester = Neo4jIngester(mock_neo4j_driver)
        
        # Simulate parse error first, then success on retry
        mock_llama_parser.parse_document.side_effect = [
            Exception("Temporary parsing error"),
            [
                {"text": "Sample document content.", "page_or_section_index": 0, "metadata": {"page": 1}}
            ]
        ]
        
        # Process document
        with patch("utils.document_parser.logger.error") as mock_error_log:
            parsed_content = parser.parse_file(sample_document_path)
            
            # Should have logged the first error
            mock_error_log.assert_called_once()
            assert "Temporary parsing error" in str(mock_error_log.call_args)
            
            # Should have succeeded on retry
            assert len(parsed_content) == 1
        
        # Simulate embedding API error, then success
        original_embed_content = mock_embedding_client.models.embed_content
        mock_embedding_client.models.embed_content.side_effect = [
            Exception("API rate limit"),
            {"embeddings": [[0.1, 0.2, 0.3, 0.4, 0.5] * 100]}
        ]
        
        # Try to embed - with patched retry mechanism
        with patch("utils.embedding.logger.warning") as mock_warning_log:
            embedding = embedding_model._get_text_embedding(parsed_content[0]["text"])
            
            # Should have logged the warning about retry
            assert mock_warning_log.called
            assert len(embedding) > 0
        
        # Reset side effect
        mock_embedding_client.models.embed_content = original_embed_content
        
        # Simulate ChromaDB error then success
        mock_collection = mock_chromadb_client.get_or_create_collection.return_value
        original_upsert = mock_collection.upsert
        mock_collection.upsert.side_effect = [
            Exception("ChromaDB temporary error"),
            None
        ]
        
        # Try to ingest to ChromaDB - with patched retry mechanism
        with patch("utils.chroma_ingester.retry") as mock_retry:
            # Configure mock retry to still call the target function
            def fake_retry(func):
                return func
            mock_retry.side_effect = fake_retry
            
            with patch("utils.chroma_ingester.logger.warning") as mock_warning_log:
                try:
                    # First call should fail
                    chroma_ingester.ingest_document(
                        doc_id="test_doc_001",
                        content=parsed_content[0]["text"],
                        embedding=embedding,
                        metadata={"filename": "test.txt"}
                    )
                except Exception:
                    pass
                
                # Reset the side effect for second call
                mock_collection.upsert = original_upsert
                
                # Second call should succeed
                chroma_ingester.ingest_document(
                    doc_id="test_doc_001",
                    content=parsed_content[0]["text"],
                    embedding=embedding,
                    metadata={"filename": "test.txt"}
                )
                
                assert mock_warning_log.called
