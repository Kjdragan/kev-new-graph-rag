"""
Embedding utility for the Graph-RAG project.
Provides embedding functionality using Google's Generative AI.
"""
import os
from typing import List, Optional, Dict, Any, Union
from google import genai

from llama_index.core.embeddings import BaseEmbedding
from loguru import logger # Use Loguru for logging

class CustomGeminiEmbedding(BaseEmbedding):
    """
    Custom embedding class that uses Google's Gemini embedding models.
    Compatible with Llama-Index's BaseEmbedding interface.
    Provides additional Gemini-specific parameters not available in standard implementations.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-embedding-exp-03-07", # Updated to user-specified model
        output_dimensionality: Optional[int] = None,
        title: Optional[str] = None,
    ) -> None:
        """
        Initialize the Google GenerativeAI embedding model.

        Args:
            api_key: Google API key, will use GOOGLE_API_KEY from environment if not provided
            model_name: Google embedding model name
            task_type: Type of task for the embedding, e.g. "RETRIEVAL_DOCUMENT" or "SEMANTIC_SIMILARITY"
            output_dimensionality: Desired dimension of embedding output vector (default is model's full dimensionality)
            title: Optional title to provide context for the embedding
        """
        # Initialize Pydantic model first
        super().__init__()

        if api_key is None:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if api_key is None:
                raise ValueError("No API key provided and GOOGLE_API_KEY not found in environment")

        # Set the model_name directly since it's part of BaseEmbedding
        self.model_name = model_name

        # Store Gemini-specific parameters as a separate config object
        # to avoid Pydantic validation errors
        self._gemini_config = {
            "output_dimensionality": output_dimensionality,
        }
        self._api_key = api_key
        self.model_name = model_name # Ensure model_name is stored
        self._gemini_config = {
            "output_dimensionality": output_dimensionality, # This might not be directly applicable to client.models.embed_content
            "title": title # This might not be directly applicable
        }
        try:
            self._client = genai.Client(api_key=self._api_key)
        except Exception as e:
            logger.error(f"Failed to initialize genai.Client: {e}", exc_info=True)
            raise

    def _get_embedding(self, text: str, task_type: Optional[str] = None) -> List[float]:
        """
        Get embedding for a single text using Google's GenerativeAI.

        Args:
            text: Text to embed

        Returns:
            List of embedding values as floats
        """
        # Extract parameters from our stored config
        # task_type is now passed as an argument
        output_dimensionality = self._gemini_config.get("output_dimensionality")
        title = self._gemini_config.get("title")

        # Set up embedding request parameters for the new SDK
        model = self.model_name
        
        # Prepare EmbedContentConfig if any specific parameters are provided
        config_params = {}
        if task_type:
            config_params["task_type"] = task_type
        if title:
            config_params["title"] = title
        if output_dimensionality:
            config_params["output_dimensionality"] = output_dimensionality

        embed_config_obj = None
        if config_params:
            embed_config_obj = genai.types.EmbedContentConfig(**config_params)
        
        try:
            logger.info(f"Requesting Gemini embedding for model: '{self.model_name}', text: '{text[:70]}...'" )
            logger.debug(f"Parameters for embed_content: model='{self.model_name}', content='{text[:70]}...', config={embed_config_obj}")

            response = self._client.models.embed_content(
                model=self.model_name,
                contents=[text],  # Use 'contents' as a list, even for a single item
                config=embed_config_obj # Pass the config object if it was created
            )
            logger.debug(f"Raw Gemini API response object for text '{text[:70]}...': {response}")

            if response:
                logger.debug("Condition: 'response' is True.")
                if hasattr(response, 'embedding'):
                    logger.debug("Condition: 'hasattr(response, 'embedding')' is True.")
                    content_embedding = response.embedding
                    logger.debug(f"Type of content_embedding: {type(content_embedding)}")
                    logger.debug(f"content_embedding object: {content_embedding}")

                    if hasattr(content_embedding, 'values'):
                        logger.debug("Condition: 'hasattr(content_embedding, 'values')' is True.")
                        logger.debug(f"Type of content_embedding.values: {type(content_embedding.values)}")
                        if isinstance(content_embedding.values, list):
                            logger.debug("Condition: 'isinstance(content_embedding.values, list)' is True.")
                            logger.debug(f"Length of content_embedding.values: {len(content_embedding.values)}")
                            # logger.debug(f"Content of content_embedding.values: {content_embedding.values}") # Potentially too verbose
                            if content_embedding.values: # Check if list is not empty before slicing
                                logger.info(f"Successfully received embedding. First 5 dims: {content_embedding.values[:5]}")
                            else:
                                logger.info("Successfully received embedding. Values list is empty.")
                            return content_embedding.values
                        else:
                            logger.warning(f"'isinstance(content_embedding.values, list)' is False. Type was: {type(content_embedding.values)}. Embedding: {content_embedding}")
                    else:
                        logger.warning(f"'hasattr(content_embedding, 'values')' is False. Embedding: {content_embedding}")
                else:
                    logger.warning(f"'hasattr(response, 'embedding')' is False. Response: {response}")
            else:
                logger.warning(f"'response' is False or None. Response: {response}")
            
            logger.error(f"Failed to extract embedding for text: {text[:100]}... Task type: {task_type}")
            return [] # Return empty list on failure

        except Exception as e:
            logger.error(f"Error during embedding generation for text '{text[:50]}...': {str(e)}", exc_info=True)
            # Re-raise the exception to allow higher-level error handling if needed, 
            # or return empty list if preferred to allow continuation.
            # For now, re-raising to make failures more visible during debugging.
            raise

    def _get_text_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text.
        Used for embedding documents.
        """
        return self._get_embedding(text, task_type="RETRIEVAL_DOCUMENT")

    def get_embedding(self, text: str) -> List[float]:
        """
        Public method to get embedding for text.
        This is needed for compatibility with code that expects this method.

        Args:
            text: Text to embed

        Returns:
            List of embedding values
        """
        return self._get_embedding(text)

    def embed_query(self, query: str) -> List[float]:
        """Embed query text. Explicitly defined to ensure availability."""
        logger.debug(f"Explicit CustomGeminiEmbedding.embed_query called for: '{query[:70]}...'" )
        return self._get_query_embedding(query)

    def _get_query_embedding(self, query: str) -> List[float]:
        """
        Get embedding for query text, implementing the BaseEmbedding interface.

        Args:
            query: Query text to embed

        Returns:
            List of embedding values
        """
        return self._get_embedding(query, task_type="RETRIEVAL_QUERY")

    async def _aget_query_embedding(self, query: str) -> List[float]:
        """
        Async version of query embedding (delegates to sync version for now).

        Args:
            query: Query text to embed

        Returns:
            List of embedding values
        """
        # For now, we use the synchronous version
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        """
        Async version of text embedding (delegates to sync version for now).

        Args:
            text: Text to embed

        Returns:
            List of embedding values
        """
        # For now, we use the synchronous version
        return self._get_text_embedding(text)
