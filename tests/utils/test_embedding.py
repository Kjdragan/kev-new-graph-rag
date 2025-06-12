"""
Unit tests for CustomGeminiEmbedding module.

These tests focus on the CustomGeminiEmbedding functionality, mocking the
Google Generative AI API to test initialization, embedding generation,
and error handling.
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

from utils.embedding import CustomGeminiEmbedding

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit

@pytest.fixture
def mock_genai_client():
    """Mock the Google GenAI client."""
    # Ensure we're patching at the correct import path where the Client is actually used
    # Using patch.object to target the specific attribute of the module
    with patch("utils.embedding.genai.Client", autospec=True) as mock_client_class:
        # Setup the mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_models = MagicMock()
        mock_client.models = mock_models
        yield mock_client_class  # Return the class itself, not the instance

@pytest.fixture
def mock_config():
    """Mock configuration values."""
    with patch("utils.embedding.get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.get_gemini_embeddings_model.return_value = "gemini-embedding-test-model"
        mock_config.get_gemini_embeddings_dimensionality.return_value = 768
        mock_get_config.return_value = mock_config
        yield mock_config


class TestCustomGeminiEmbedding:
    """Test cases for CustomGeminiEmbedding class."""

    def test_initialization_with_defaults(self, mock_genai_client, mock_config, monkeypatch):
        """Test initialization with default values from config."""
        # Set environment variable
        monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key")
        
        # Initialize the embedding model
        embedding_model = CustomGeminiEmbedding()
        
        # Assertions
        assert embedding_model.model_name == "gemini-embedding-test-model"
        assert embedding_model._gemini_config["output_dimensionality"] == 768
        assert embedding_model._google_api_key == "test-api-key"
        assert embedding_model._gemini_config["project_id"] == "neo4j-deployment-new1"
        
        # Check that client was initialized with the API key
        mock_genai_client.assert_called_once_with(api_key="test-api-key")

    def test_initialization_with_custom_values(self, mock_genai_client):
        """Test initialization with custom values overriding defaults."""
        # Initialize with custom values
        embedding_model = CustomGeminiEmbedding(
            google_api_key="custom-api-key",
            model_name="custom-model-name",
            output_dimensionality=1024,
            title="Custom Title",
            project_id="custom-project",
            task_type="SEMANTIC_SIMILARITY"
        )
        
        # Assertions
        assert embedding_model.model_name == "custom-model-name"
        assert embedding_model._gemini_config["output_dimensionality"] == 1024
        assert embedding_model._google_api_key == "custom-api-key"
        assert embedding_model._gemini_config["title"] == "Custom Title"
        assert embedding_model._gemini_config["project_id"] == "custom-project"
        assert embedding_model._gemini_config["task_type"] == "SEMANTIC_SIMILARITY"

    def test_initialization_missing_api_key(self, mock_genai_client, monkeypatch):
        """Test initialization fails when API key is missing."""
        # Remove environment variable if exists
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        
        # Initialization should fail
        with pytest.raises(ValueError, match="No Google API key provided"):
            CustomGeminiEmbedding()

    def test_initialization_client_failure(self, monkeypatch):
        """Test error handling when client initialization fails."""
        # Set environment variable
        monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key")
        
        # Mock client to raise an exception
        with patch("utils.embedding.genai.Client") as mock_client_class:
            mock_client_class.side_effect = Exception("API client initialization failed")
            
            # Initialization should propagate the exception
            with pytest.raises(Exception, match="API client initialization failed"):
                CustomGeminiEmbedding()

    def test_get_embedding_success(self, mock_genai_client):
        """Test successful embedding generation."""
        # Mock embedding response
        mock_embedding_values = [0.1, 0.2, 0.3, 0.4]
        mock_embedding_response = MagicMock()
        mock_embedding_obj = MagicMock()
        mock_embedding_obj.values = mock_embedding_values
        mock_embedding_response.embeddings = [mock_embedding_obj]
        
        # Create a new mock client for the internal client creation
        mock_internal_client = MagicMock()
        mock_internal_client_instance = MagicMock()
        mock_internal_client.return_value = mock_internal_client_instance
        mock_internal_client_instance.models.embed_content.return_value = mock_embedding_response
        
        # Patch the internal genai.Client creation
        with patch('utils.embedding.genai.Client', mock_internal_client):
            # Initialize and call the embedding method
            embedding_model = CustomGeminiEmbedding(google_api_key="test-api-key")
            result = embedding_model._get_embedding("Test text")
        
        # Assertions
        assert result == mock_embedding_values
        mock_internal_client_instance.models.embed_content.assert_called_once()
        _, kwargs = mock_internal_client_instance.models.embed_content.call_args
        assert kwargs["contents"] == "Test text"
        assert kwargs["model"] == "gemini-embedding-001"  # Updated to match the actual model name used

    def test_get_embedding_with_task_type(self, mock_genai_client):
        """Test embedding generation with specific task type."""
        # Mock embedding response
        mock_embedding_values = [0.1, 0.2, 0.3, 0.4]
        mock_embedding_response = MagicMock()
        mock_embedding_obj = MagicMock()
        mock_embedding_obj.values = mock_embedding_values
        mock_embedding_response.embeddings = [mock_embedding_obj]

        # Create a new mock client for the internal client creation
        mock_internal_client = MagicMock()
        mock_internal_client_instance = MagicMock()
        mock_internal_client.return_value = mock_internal_client_instance
        mock_internal_client_instance.models.embed_content.return_value = mock_embedding_response

        # Patch the internal genai.Client creation
        with patch('utils.embedding.genai.Client', mock_internal_client):
            # Initialize and call the embedding method with task type
            embedding_model = CustomGeminiEmbedding(google_api_key="test-api-key")
            result = embedding_model._get_embedding("Test text", task_type="RETRIEVAL_QUERY")

        # Assertions
        assert result == mock_embedding_values
        mock_internal_client_instance.models.embed_content.assert_called_once()
        _, kwargs = mock_internal_client_instance.models.embed_content.call_args
        assert kwargs["contents"] == "Test text"
        assert kwargs["model"] == "gemini-embedding-001"
        assert kwargs["config"].task_type == "RETRIEVAL_QUERY"

    def test_get_text_embedding(self, mock_genai_client):
        """Test specialized text embedding method."""
        # Mock embedding response
        mock_embedding_values = [0.1, 0.2, 0.3, 0.4]
        mock_embedding_response = MagicMock()
        mock_embedding_obj = MagicMock()
        mock_embedding_obj.values = mock_embedding_values
        mock_embedding_response.embeddings = [mock_embedding_obj]
        
        # Create a new mock client for the internal client creation
        mock_internal_client = MagicMock()
        mock_internal_client_instance = MagicMock()
        mock_internal_client.return_value = mock_internal_client_instance
        mock_internal_client_instance.models.embed_content.return_value = mock_embedding_response

        # Patch the internal genai.Client creation
        with patch('utils.embedding.genai.Client', mock_internal_client):
            # Initialize and call the text embedding method
            embedding_model = CustomGeminiEmbedding(google_api_key="test-api-key")
            result = embedding_model._get_text_embedding("Test document text")

        # Assertions
        assert result == mock_embedding_values
        mock_internal_client_instance.models.embed_content.assert_called_once()
        _, kwargs = mock_internal_client_instance.models.embed_content.call_args
        assert kwargs["contents"] == "Test document text"
        assert kwargs["model"] == "gemini-embedding-001"
        assert kwargs["config"].task_type == "RETRIEVAL_DOCUMENT"

    def test_get_query_embedding(self, mock_genai_client):
        """Test specialized query embedding method."""
        # Mock embedding response
        mock_embedding_values = [0.1, 0.2, 0.3, 0.4]
        mock_embedding_response = MagicMock()
        mock_embedding_obj = MagicMock()
        mock_embedding_obj.values = mock_embedding_values
        mock_embedding_response.embeddings = [mock_embedding_obj]

        # Create a new mock client for the internal client creation
        mock_internal_client = MagicMock()
        mock_internal_client_instance = MagicMock()
        mock_internal_client.return_value = mock_internal_client_instance
        mock_internal_client_instance.models.embed_content.return_value = mock_embedding_response

        # Patch the internal genai.Client creation
        with patch('utils.embedding.genai.Client', mock_internal_client):
            # Initialize and call the query embedding method
            embedding_model = CustomGeminiEmbedding(google_api_key="test-api-key")
            result = embedding_model._get_query_embedding("Test query text")

        # Assertions
        assert result == mock_embedding_values
        mock_internal_client_instance.models.embed_content.assert_called_once()
        _, kwargs = mock_internal_client_instance.models.embed_content.call_args
        assert kwargs["contents"] == "Test query text"
        assert kwargs["model"] == "gemini-embedding-001"
        assert kwargs["config"].task_type == "RETRIEVAL_QUERY"

    def test_embed_query_public_method(self, mock_genai_client):
        """Test the public embed_query method."""
        # Mock embedding response
        mock_embedding_values = [0.1, 0.2, 0.3, 0.4]
        mock_embedding_response = MagicMock()
        mock_embedding_obj = MagicMock()
        mock_embedding_obj.values = mock_embedding_values
        mock_embedding_response.embeddings = [mock_embedding_obj]

        # Create a new mock client for the internal client creation
        mock_internal_client = MagicMock()
        mock_internal_client_instance = MagicMock()
        mock_internal_client.return_value = mock_internal_client_instance
        mock_internal_client_instance.models.embed_content.return_value = mock_embedding_response

        # Patch the internal genai.Client creation
        with patch('utils.embedding.genai.Client', mock_internal_client):
            # Initialize and call the public embed_query method
            embedding_model = CustomGeminiEmbedding(google_api_key="test-api-key")
            result = embedding_model.embed_query("Test query")

        # Assertions
        assert result == mock_embedding_values
        mock_internal_client_instance.models.embed_content.assert_called_once()
        _, kwargs = mock_internal_client_instance.models.embed_content.call_args
        assert kwargs["contents"] == "Test query"
        assert kwargs["model"] == "gemini-embedding-001"
        assert kwargs["config"].task_type == "RETRIEVAL_QUERY"

    def test_error_response_handling(self, mock_genai_client):
        """Test handling of error responses from the API."""
        # Mock error response
        error_response = {
            'error': {
                'code': 400,
                'message': 'Invalid request'
            }
        }
        
        # Setup the mock client to return the error response
        mock_genai_client.models.embed_content.return_value = error_response
        
        # Initialize and test error handling
        embedding_model = CustomGeminiEmbedding(google_api_key="test-api-key")
        with pytest.raises(ValueError, match="API error during embedding generation"):
            embedding_model._get_embedding("Test text")

    def test_unexpected_response_format(self, mock_genai_client):
        """Test handling of unexpected response format."""
        # Mock unexpected response
        unexpected_response = {"unexpected_key": "unexpected_value"}
        
        # Setup the mock client to return the unexpected response
        mock_genai_client.models.embed_content.return_value = unexpected_response
        
        # Initialize and test error handling
        embedding_model = CustomGeminiEmbedding(google_api_key="test-api-key")
        with pytest.raises(ValueError, match="Could not extract embedding from response"):
            embedding_model._get_embedding("Test text")

    def test_embedding_dict_response_format(self, mock_genai_client):
        """Test handling of embedding in dictionary format."""
        # Mock dict response with 'embedding' key
        embedding_values = [0.1, 0.2, 0.3, 0.4]
        dict_response = {"embedding": embedding_values}
        
        # Setup the mock client to return the dict response
        mock_genai_client.models.embed_content.return_value = dict_response
        
        # Initialize and test response parsing
        embedding_model = CustomGeminiEmbedding(google_api_key="test-api-key")
        result = embedding_model._get_embedding("Test text")
        
        # Assertions
        assert result == embedding_values

    def test_embeddings_dict_response_format(self, mock_genai_client):
        """Test handling of embeddings list in dictionary format."""
        # Mock dict response with 'embeddings' key
        embedding_values = [0.1, 0.2, 0.3, 0.4]
        dict_response = {"embeddings": [embedding_values]}
        
        # Setup the mock client to return the dict response
        mock_genai_client.models.embed_content.return_value = dict_response
        
        # Initialize and test response parsing
        embedding_model = CustomGeminiEmbedding(google_api_key="test-api-key")
        result = embedding_model._get_embedding("Test text")
        
        # Assertions
        assert result == embedding_values

    def test_api_exception_handling(self, mock_genai_client):
        """Test handling of API exceptions during embedding generation."""
        # Setup the mock client to raise an exception
        mock_genai_client.models.embed_content.side_effect = Exception("API error")
        
        # Initialize and test exception handling
        embedding_model = CustomGeminiEmbedding(google_api_key="test-api-key")
        with pytest.raises(Exception, match="API error"):
            embedding_model._get_embedding("Test text")
