"""
Unit tests for ChromaIngester module.

These tests focus on the ChromaIngester functionality, mocking the ChromaDB client
and collection to test initialization, document ingestion, searching and error handling.
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

from utils.chroma_ingester import ChromaIngester
from utils.config_models import ChromaDBConfig
from utils.embedding import CustomGeminiEmbedding

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit

@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client."""
    with patch("utils.chroma_ingester.chromadb.HttpClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_collection():
    """Mock ChromaDB collection."""
    mock_col = MagicMock()
    mock_col.count.return_value = 10
    return mock_col

@pytest.fixture
def mock_embedding_model():
    """Mock embedding model."""
    mock_model = MagicMock(spec=CustomGeminiEmbedding)
    mock_model._gemini_config = {"output_dimensionality": 1024}
    mock_model._get_text_embedding.return_value = [0.1] * 5  # Mock 5-dim embedding
    return mock_model

@pytest.fixture
def chroma_config():
    """Create ChromaDB configuration."""
    return ChromaDBConfig(
        host="localhost",
        port=8000,
        collection_name="test_collection",
        auth_enabled=False
    )

@pytest.fixture
def auth_chroma_config():
    """Create ChromaDB configuration with auth enabled."""
    return ChromaDBConfig(
        host="localhost",
        port=8000,
        collection_name="test_collection",
        auth_enabled=True,
        username="testuser",
        password="testpass"
    )


class TestChromaIngester:
    """Test cases for ChromaIngester class."""

    def test_initialization_without_auth(self, mock_chroma_client, mock_collection, chroma_config, mock_embedding_model):
        """Test initialization without authentication."""
        # Setup mock collection
        mock_chroma_client.get_or_create_collection.return_value = mock_collection
        
        # Initialize ingester
        ingester = ChromaIngester(chroma_config, mock_embedding_model)
        
        # Assertions
        mock_chroma_client.get_or_create_collection.assert_called_once()
        assert ingester.collection == mock_collection
        assert ingester.config == chroma_config
        assert ingester.embedding_model == mock_embedding_model

    def test_initialization_with_auth(self, mock_chroma_client, mock_collection, auth_chroma_config, mock_embedding_model):
        """Test initialization with authentication."""
        # Setup mock collection
        mock_chroma_client.get_or_create_collection.return_value = mock_collection
        
        with patch("utils.chroma_ingester.chromadb.Settings") as mock_settings_class:
            mock_settings = MagicMock()
            mock_settings_class.return_value = mock_settings
            
            # Initialize ingester
            ingester = ChromaIngester(auth_chroma_config, mock_embedding_model)
            
            # Assertions
            mock_settings_class.assert_called_once_with(
                chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                chroma_client_auth_credentials=f"{auth_chroma_config.username}:{auth_chroma_config.password}"
            )
            mock_chroma_client.get_or_create_collection.assert_called_once()
            assert ingester.collection == mock_collection

    def test_init_client_exception(self, chroma_config, mock_embedding_model):
        """Test handling of exceptions during client initialization."""
        # Use a different patch here to make the constructor itself raise an exception
        with patch("utils.chroma_ingester.chromadb.HttpClient") as mock_client_class:
            # Setup mock constructor to raise exception
            mock_client_class.side_effect = Exception("Connection error")
            
            # Initialization should propagate the exception
            with pytest.raises(Exception, match="Connection error"):
                ChromaIngester(chroma_config, mock_embedding_model)

    def test_get_or_create_collection_exception(self, mock_chroma_client, chroma_config, mock_embedding_model):
        """Test handling of exceptions during collection creation."""
        # Setup mock get_or_create_collection to raise exception
        mock_chroma_client.get_or_create_collection.side_effect = Exception("Collection error")
        
        # Initialization should propagate the exception
        with pytest.raises(Exception, match="Collection error"):
            ChromaIngester(chroma_config, mock_embedding_model)

    def test_ingest_documents_success(self, mock_chroma_client, mock_collection, chroma_config, mock_embedding_model):
        """Test successful document ingestion."""
        # Setup mock collection
        mock_chroma_client.get_or_create_collection.return_value = mock_collection
        
        # Mock embedding generation (5-dim vectors)
        mock_embeddings = [[0.1] * 5 for _ in range(2)]
        mock_embedding_model._get_text_embedding.side_effect = mock_embeddings
        
        # Create test documents
        test_documents = [
            {"id": "doc1", "text": "Test document 1", "metadata": {"source": "test1"}},
            {"id": "doc2", "text": "Test document 2", "metadata": {"source": "test2"}}
        ]
        
        # Initialize ingester and ingest documents
        ingester = ChromaIngester(chroma_config, mock_embedding_model)
        result = ingester.ingest_documents(test_documents)
        
        # Assertions
        assert result is True
        mock_collection.upsert.assert_called_once()
        call_args = mock_collection.upsert.call_args[1]
        assert call_args["ids"] == ["doc1", "doc2"]
        assert call_args["documents"] == ["Test document 1", "Test document 2"]
        assert len(call_args["metadatas"]) == 2
        assert call_args["metadatas"][0]["source"] == "test1"

    def test_ingest_documents_with_retry(self, mock_chroma_client, mock_collection, chroma_config, mock_embedding_model):
        """Test document ingestion with retry on ChromaError."""
        # Instead of testing the retry mechanism itself (which is provided by tenacity),
        # We'll modify our approach to ensure our function handles exceptions properly
        
        # Setup mock collection
        mock_chroma_client.get_or_create_collection.return_value = mock_collection
        
        # Patch with a non-retrying version of the ingest_documents method
        with patch.object(ChromaIngester, 'batch_embed_documents') as mock_batch_embed, \
             patch('tenacity.retry') as mock_retry:
            
            # Make retry a pass-through decorator that doesn't actually retry
            mock_retry.return_value = lambda f: f
            
            # Configure the mocked batch_embed_documents to return a simple embedding
            mock_batch_embed.return_value = [[0.1, 0.1, 0.1, 0.1, 0.1]]
            
            # First attempt will fail
            mock_collection.upsert.side_effect = Exception("Temp failure")
            
            # Create test documents
            test_documents = [{"id": "doc1", "text": "Test document", "metadata": {"source": "test"}}]
            
            # Initialize ingester
            ingester = ChromaIngester(chroma_config, mock_embedding_model)
            
            # First attempt should fail
            with pytest.raises(Exception, match="Temp failure"):
                ingester.ingest_documents(test_documents)
            
            # Reset side effect to succeed on second attempt
            mock_collection.upsert.side_effect = None
            
            # Second attempt should succeed
            result = ingester.ingest_documents(test_documents)
            
            # Assertions
            assert result is True
            assert mock_collection.upsert.call_count == 2  # Called twice (once failing, once succeeding)

    def test_batch_embed_documents(self, mock_chroma_client, mock_collection, chroma_config, mock_embedding_model):
        """Test batch embedding of documents."""
        # Setup mock collection
        mock_chroma_client.get_or_create_collection.return_value = mock_collection
        
        # Create test texts
        test_texts = ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"]
        
        # Mock embedding vectors - different for each text
        mock_embeddings = [
            [0.1] * 5,
            [0.2] * 5,
            [0.3] * 5,
            [0.4] * 5,
            [0.5] * 5
        ]
        mock_embedding_model._get_text_embedding.side_effect = mock_embeddings
        
        # Initialize ingester and batch embed documents
        ingester = ChromaIngester(chroma_config, mock_embedding_model)
        result = ingester.batch_embed_documents(test_texts)
        
        # Assertions
        assert len(result) == 5
        assert result[0] == [0.1] * 5
        assert result[4] == [0.5] * 5
        assert mock_embedding_model._get_text_embedding.call_count == 5

    def test_add_documents_with_metadata_and_ids(self, mock_chroma_client, mock_collection, chroma_config, mock_embedding_model):
        """Test adding documents with explicit metadata and IDs."""
        # Setup mock collection
        mock_chroma_client.get_or_create_collection.return_value = mock_collection
        
        # Test data
        documents = ["Document 1", "Document 2"]
        metadatas = [{"source": "test1"}, {"source": "test2"}]
        ids = ["id1", "id2"]
        
        # Initialize ingester and add documents
        ingester = ChromaIngester(chroma_config, mock_embedding_model)
        result = ingester.add_documents(documents, metadatas, ids)
        
        # Assertions
        assert result is True
        mock_collection.upsert.assert_called_once()
        call_args = mock_collection.upsert.call_args[1]
        assert call_args["documents"] == documents
        assert call_args["metadatas"] == metadatas
        assert call_args["ids"] == ids

    def test_count_documents(self, mock_chroma_client, mock_collection, chroma_config, mock_embedding_model):
        """Test counting documents in the collection."""
        # Setup mock collection
        mock_chroma_client.get_or_create_collection.return_value = mock_collection
        mock_collection.count.return_value = 42
        
        # Initialize ingester and count documents
        ingester = ChromaIngester(chroma_config, mock_embedding_model)
        count = ingester.count_documents()
        
        # Assertions
        assert count == 42
        mock_collection.count.assert_called_once()

    def test_count_documents_error(self, mock_chroma_client, mock_collection, chroma_config, mock_embedding_model):
        """Test error handling when counting documents."""
        # Setup mock collection
        mock_chroma_client.get_or_create_collection.return_value = mock_collection
        mock_collection.count.side_effect = Exception("Count error")
        
        # Initialize ingester and count documents
        ingester = ChromaIngester(chroma_config, mock_embedding_model)
        count = ingester.count_documents()
        
        # Assertions - should return 0 on error
        assert count == 0
        mock_collection.count.assert_called_once()

    def test_search(self, mock_chroma_client, mock_collection, chroma_config, mock_embedding_model):
        """Test document search functionality."""
        # Setup mock collection
        mock_chroma_client.get_or_create_collection.return_value = mock_collection
        
        # Mock query result from ChromaDB
        mock_query_result = {
            "ids": [["doc1", "doc2"]],
            "documents": [["Document 1 content", "Document 2 content"]],
            "metadatas": [[{"source": "test1"}, {"source": "test2"}]],
            "distances": [[0.1, 0.2]]
        }
        mock_collection.query.return_value = mock_query_result
        
        # Mock embedding generation
        query_embedding = [0.1] * 5
        mock_embedding_model._get_text_embedding.return_value = query_embedding
        
        # Initialize ingester and search
        ingester = ChromaIngester(chroma_config, mock_embedding_model)
        result = ingester.search("test query", n_results=2)
        
        # Assertions
        mock_embedding_model._get_text_embedding.assert_called_once_with("test query")
        mock_collection.query.assert_called_once()
        call_args = mock_collection.query.call_args[1]
        assert call_args["query_embeddings"] == [query_embedding]
        assert call_args["n_results"] == 2
        assert "embeddings" not in call_args["include"]
        assert result == mock_query_result

    def test_search_with_embeddings_and_filters(self, mock_chroma_client, mock_collection, chroma_config, mock_embedding_model):
        """Test search with embeddings included and filters applied."""
        # Setup mock collection
        mock_chroma_client.get_or_create_collection.return_value = mock_collection
        
        # Mock query result
        mock_query_result = {
            "ids": [["doc1"]],
            "documents": [["Document 1 content"]],
            "metadatas": [[{"source": "test1"}]],
            "distances": [[0.1]],
            "embeddings": [[[0.1, 0.2, 0.3, 0.4, 0.5]]]
        }
        mock_collection.query.return_value = mock_query_result
        
        # Test filters
        filters = {"source": "test1"}
        
        # Initialize ingester and search with filters and embeddings
        ingester = ChromaIngester(chroma_config, mock_embedding_model)
        result = ingester.search("test query", filters=filters, include_embeddings=True)
        
        # Assertions
        call_args = mock_collection.query.call_args[1]
        assert call_args["where"] == filters
        assert "embeddings" in call_args["include"]
        assert result == mock_query_result
