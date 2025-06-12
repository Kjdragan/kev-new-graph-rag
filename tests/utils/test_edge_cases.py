"""
Edge case tests for the Graph RAG system.

These tests focus on challenging scenarios such as large documents,
unusual input formats, and API rate limiting.
"""
import os
import sys
import pytest
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

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit


class TestLargeDocumentHandling:
    """Test how the system handles unusually large documents."""
    
    def test_large_document_parsing(self):
        """Test parsing of extremely large documents."""
        # Create a mock LlamaParser
        with patch("utils.document_parser.LlamaParse") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            
            # Create a large number of pages to simulate a large document
            large_doc_pages = []
            for i in range(1000):  # 1000 pages
                large_doc_pages.append({
                    "text": f"Content for page {i}. " * 50,  # ~500 chars per page
                    "page_or_section_index": i,
                    "metadata": {"page": i+1}
                })
                
            # Setup mock to return the large document
            mock_parser.parse_document.return_value = large_doc_pages
            
            # Initialize the parser and parse a dummy file
            parser = DocumentParser(config=LlamaParseConfig(api_key="test-api-key"))
            
            # Use temp file path for testing
            dummy_path = Path("dummy_large_doc.pdf")
            
            # Parse the "large" document
            parsed_content = parser.parse_file(dummy_path)
            
            # Verify all pages were processed
            assert len(parsed_content) == 1000
            
            # Test concatenation method with large document
            concatenated_text = parser.parse_file_to_concatenated_text(dummy_path)
            
            # Verify the concatenated text exists and has substantial length
            assert len(concatenated_text) > 100000  # Should be ~500,000 chars
    
    def test_large_embedding_vector_handling(self):
        """Test handling of unusually large embedding vectors."""
        with patch("utils.embedding.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Create an abnormally large embedding vector
            # Normal is ~1500 dimensions, test with 5000
            large_embedding = [0.1] * 5000
            
            # Setup the mock to return the large embedding
            mock_client.models.embed_content.return_value = {
                "embeddings": [large_embedding]
            }
            
            # Initialize embedding model
            embedding_model = CustomGeminiEmbedding(google_api_key="test-api-key")
            
            # Get embedding
            result = embedding_model._get_embedding("Test text")
            
            # Verify the large embedding was returned correctly
            assert len(result) == 5000
            
            # Test with Neo4j ingester to ensure it can handle large vectors
            with patch("neo4j.Driver") as mock_driver_class:
                mock_driver = MagicMock()
                mock_driver_class.return_value = mock_driver
                
                # Initialize Neo4j ingester
                neo4j_ingester = Neo4jIngester(mock_driver)
                
                # Create document data with large embedding
                doc_data = DocumentIngestionData(
                    doc_id="large_embedding_test",
                    filename="test.txt",
                    content="Test content",
                    embedding=large_embedding,
                    source_type="test",
                    mime_type="text/plain",
                    parsed_timestamp=None,
                    metadata={}
                )
                
                # Ingest the document
                neo4j_ingester.ingest_document(doc_data)
                
                # Verify the session.run was called
                mock_session = mock_driver.session.return_value.__enter__.return_value
                mock_session.run.assert_called_once()
                
                # Check that embedding was passed correctly
                args, kwargs = mock_session.run.call_args
                assert len(kwargs["embedding"]) == 5000


class TestUnusualInputFormats:
    """Test how the system handles unusual or malformed input formats."""
    
    def test_empty_document_handling(self):
        """Test handling of empty documents."""
        # Create mock for LlamaParse
        with patch("utils.document_parser.LlamaParse") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            
            # Return empty list to simulate empty document
            mock_parser.parse_document.return_value = []
            
            # Initialize the parser
            parser = DocumentParser(config=LlamaParseConfig(api_key="test-api-key"))
            
            # Use temp file path for testing
            dummy_path = Path("empty_doc.pdf")
            
            # Parse the "empty" document
            parsed_content = parser.parse_file(dummy_path)
            
            # Should return empty list
            assert len(parsed_content) == 0
            
            # Test concatenation with empty doc
            with patch("utils.document_parser.logger.warning") as mock_warning:
                concatenated_text = parser.parse_file_to_concatenated_text(dummy_path)
                
                # Should return empty string
                assert concatenated_text == ""
                
                # Should log warning about empty document
                mock_warning.assert_called_once()
    
    def test_malformed_document_handling(self):
        """Test handling of malformed document structures."""
        # Create mock for LlamaParse
        with patch("utils.document_parser.LlamaParse") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            
            # Return malformed data without expected keys
            mock_parser.parse_document.return_value = [
                {"unexpected_key": "value"},
                {"another_key": 123, "no_text_here": True}
            ]
            
            # Initialize the parser
            parser = DocumentParser(config=LlamaParseConfig(api_key="test-api-key"))
            
            # Use temp file path for testing
            dummy_path = Path("malformed_doc.pdf")
            
            # Parse the malformed document with logger patch
            with patch("utils.document_parser.logger.warning") as mock_warning:
                parsed_content = parser.parse_file(dummy_path)
                
                # Should have returned the malformed content as-is
                assert len(parsed_content) == 2
                
                # Should have logged warnings about missing text
                assert mock_warning.call_count > 0
            
            # Test concatenation with malformed doc
            with patch("utils.document_parser.logger.warning") as mock_warning:
                concatenated_text = parser.parse_file_to_concatenated_text(dummy_path)
                
                # Should return empty string since no text field exists
                assert concatenated_text == ""
                
                # Should log warning
                mock_warning.assert_called_once()
    
    def test_extremely_short_text_embedding(self):
        """Test embedding of extremely short text."""
        with patch("utils.embedding.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Setup the mock to return a normal embedding
            mock_client.models.embed_content.return_value = {
                "embeddings": [[0.1, 0.2, 0.3, 0.4, 0.5] * 100]
            }
            
            # Initialize embedding model
            embedding_model = CustomGeminiEmbedding(google_api_key="test-api-key")
            
            # Test with empty string
            empty_result = embedding_model._get_embedding("")
            
            # Should still return embedding
            assert len(empty_result) > 0
            
            # Test with single character
            char_result = embedding_model._get_embedding("a")
            
            # Should still return embedding
            assert len(char_result) > 0
            
            # Test with whitespace only
            space_result = embedding_model._get_embedding("   \n\t  ")
            
            # Should still return embedding
            assert len(space_result) > 0


class TestRateLimitHandling:
    """Test handling of API rate limits and backoff strategies."""
    
    def test_llamaparse_rate_limit_handling(self):
        """Test handling of LlamaParse rate limits."""
        # Create mock for LlamaParse
        with patch("utils.document_parser.LlamaParse") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            
            # Setup side effects to simulate rate limit then success
            rate_limit_error = Exception("429 Rate limit exceeded")
            success_response = [{"text": "Content", "page_or_section_index": 0, "metadata": {}}]
            
            mock_parser.parse_document.side_effect = [
                rate_limit_error, 
                rate_limit_error, 
                success_response
            ]
            
            # Initialize the parser
            parser = DocumentParser(config=LlamaParseConfig(api_key="test-api-key"))
            
            # Use temp file path for testing
            dummy_path = Path("rate_limited_doc.pdf")
            
            # Test with patched retry decorator to capture retries
            # In real scenario, the retry decorator in the DocumentParser would handle this
            with patch("utils.document_parser.retry") as mock_retry:
                # Configure mock retry to use a fake decorator that still calls the target
                # but allows us to track calls
                retry_count = 0
                
                def fake_retry(func):
                    def wrapped(*args, **kwargs):
                        nonlocal retry_count
                        try:
                            return func(*args, **kwargs)
                        except Exception as e:
                            retry_count += 1
                            if retry_count < 3:
                                raise e
                            return success_response
                    return wrapped
                
                mock_retry.side_effect = lambda *args, **kwargs: fake_retry
                
                # Parse the document, should succeed after retries
                result = parser.parse_file(dummy_path)
                
                # Should have the successful result
                assert len(result) == 1
                assert result[0]["text"] == "Content"
                
                # Should have retried twice
                assert retry_count == 2
    
    def test_embedding_rate_limit_handling(self):
        """Test handling of embedding API rate limits."""
        with patch("utils.embedding.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Setup side effects to simulate rate limit then success
            rate_limit_error = Exception("Rate limit exceeded")
            success_response = {"embeddings": [[0.1, 0.2, 0.3, 0.4, 0.5]]}
            
            mock_client.models.embed_content.side_effect = [
                rate_limit_error,
                rate_limit_error,
                success_response
            ]
            
            # Initialize embedding model
            embedding_model = CustomGeminiEmbedding(google_api_key="test-api-key")
            
            # Setup manual retry handling (in real code, would use tenacity)
            retry_attempts = 0
            max_retries = 3
            
            # Attempt to get embedding with retries
            while retry_attempts < max_retries:
                try:
                    result = embedding_model._get_embedding("Test text")
                    # If we get here, succeeded
                    break
                except Exception:
                    retry_attempts += 1
                    if retry_attempts >= max_retries:
                        raise
            
            # Should have succeeded on the 3rd try
            assert retry_attempts == 2
            assert len(result) == 5
