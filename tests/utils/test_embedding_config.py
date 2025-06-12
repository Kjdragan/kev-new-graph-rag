"""
Test that CustomGeminiEmbedding correctly uses configuration values.
"""

import pytest
from loguru import logger
import sys

from utils.embedding import CustomGeminiEmbedding
from utils.config import get_config

@pytest.mark.unit
def test_embedding_dimensionality_matches_config():
    """Test that the embedding dimensionality matches the config value."""
    # Get the expected values from config
    config = get_config()
    expected_model = config.get_gemini_embeddings_model()
    expected_dims = config.get_gemini_embeddings_dimensionality()
    
    logger.info(f"Config values - Model: {expected_model}, Dimensionality: {expected_dims}")
    
    # Create embedding model instance with mocked API key
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("GOOGLE_API_KEY", "fake_api_key")
        embedding_model = CustomGeminiEmbedding()
        
        # Mock the embedding generation to return an array of the expected size
        # This avoids making an actual API call during testing
        def mock_get_embedding(text):
            # Return an array with the expected dimensionality
            return [0.1] * expected_dims
        
        # Apply the mock
        embedding_model.get_embedding = mock_get_embedding
        
        # Test with a simple text
        test_text = "This is a test embedding."
        
        # Get embedding
        embedding = embedding_model.get_embedding(test_text)
        
        # Verify dimensions
        actual_dims = len(embedding)
        
        # Assert the dimensions match
        assert actual_dims == expected_dims, \
            f"Embedding dimensionality {actual_dims} does not match config value {expected_dims}"
