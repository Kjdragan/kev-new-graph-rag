"""
Simple test script to verify that CustomGeminiEmbedding uses config values.
"""

import os
import sys
from loguru import logger

# Configure logger to show debug messages
logger.remove()
logger.add(sys.stderr, level="DEBUG")

# Import the embedding class
from utils.embedding import CustomGeminiEmbedding
from utils.config import get_config

def main():
    logger.info("Testing CustomGeminiEmbedding with config values")
    
    # Get the expected values from config
    config = get_config()
    expected_model = config.get_gemini_embeddings_model()
    expected_dims = config.get_gemini_embeddings_dimensionality()
    
    logger.info(f"Config values - Model: {expected_model}, Dimensionality: {expected_dims}")
    
    # Create embedding model instance
    embedding_model = CustomGeminiEmbedding()
    
    # Test with a simple text
    test_text = "This is a test embedding."
    logger.info(f"Generating embedding for: '{test_text}'")
    
    # Get embedding
    embedding = embedding_model.get_embedding(test_text)
    
    # Verify length
    actual_dims = len(embedding)
    logger.info(f"Embedding generated: {len(embedding)} dimensions")
    logger.info(f"First few values: {embedding[:5]}")
    
    # Verify against config
    if actual_dims == expected_dims:
        logger.success(f"✅ Success! Embedding dimensionality matches config: {actual_dims} = {expected_dims}")
    else:
        logger.error(f"❌ Error! Embedding dimensionality {actual_dims} does not match config value {expected_dims}")
    
    return actual_dims == expected_dims

if __name__ == "__main__":
    main()
