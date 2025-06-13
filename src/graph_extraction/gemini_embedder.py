"""
Custom implementation of GeminiEmbedder that handles the batch size=1 constraint
of the Gemini embedding API.
"""
import asyncio
from typing import List, Any

from google import genai
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from loguru import logger

def truncate_embedding(embedding: Any, max_length: int = 100) -> str:
    """
    Truncate embedding vector representation to a specified length for readability in logs.
    
    Args:
        embedding: The embedding vector or list to truncate
        max_length: Maximum length of the string representation
        
    Returns:
        Truncated string representation of the embedding
    """
    embedding_str = str(embedding)
    if len(embedding_str) <= max_length:
        return embedding_str
    return embedding_str[:max_length] + '...'

class BatchSizeOneGeminiEmbedder(GeminiEmbedder):
    """
    Extended version of GeminiEmbedder that handles the batch size=1 constraint
    by processing items one at a time in parallel.
    """
    
    async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
        """
        Create embeddings for a batch of input data by processing each item individually.
        
        Args:
            input_data_list: List of strings to create embeddings for.
            
        Returns:
            List of embedding vectors (each a list of floats).
        """
        logger.debug(f"Creating batch embeddings for {len(input_data_list)} items one by one")
        
        # Process each item individually in parallel
        tasks = [self.create(input_data) for input_data in input_data_list]
        embeddings = await asyncio.gather(*tasks)
        
        # Log with truncated embedding representation for readability
        if embeddings and len(embeddings) > 0:
            sample_embedding = embeddings[0]
            truncated = truncate_embedding(sample_embedding)
            logger.debug(f"Successfully created {len(embeddings)} embeddings. Sample (truncated): {truncated}")
        else:
            logger.debug(f"Successfully created {len(embeddings)} embeddings")
            
        return embeddings
