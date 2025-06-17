"""
Embedding utility for the Graph-RAG project.
Provides embedding functionality using Google's Generative AI.
"""
import os
import sys
from typing import List, Optional, Dict, Any, Union
from google import genai

from llama_index.core.embeddings import BaseEmbedding
from loguru import logger # Use Loguru for logging
from .config_loader import get_config

# Try to import the truncate_embedding function from gemini_embedder if available
try:
    from src.graph_extraction.gemini_embedder import truncate_embedding
except ImportError:
    # Define the function locally if import fails
    def truncate_embedding(embedding: Any, max_length: int = 100) -> str:
        """
        Truncate embedding vector representation to a specified length for readability in logs.
        
        Args:
            embedding: The embedding vector or list to truncate
            max_length: Maximum length of the string representation
            
        Returns:
            Truncated string representation of the embedding
        """
        # Handle None case
        if embedding is None:
            return "None"
            
        # Convert to string representation
        embedding_str = str(embedding)
        
        # Check if already short enough
        if len(embedding_str) <= max_length:
            return embedding_str
            
        # Truncate and add ellipsis
        return embedding_str[:max_length] + '...'

class CustomGeminiEmbedding(BaseEmbedding):
    """
    Custom embedding class that uses Google's Gemini embedding models.
    Compatible with Llama-Index's BaseEmbedding interface.
    Provides additional Gemini-specific parameters not available in standard implementations.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        output_dimensionality: Optional[int] = None,
        title: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> None:
        """
        Initialize the Google GenerativeAI embedding model using Application Default Credentials (ADC).

        This method relies on environment variables for configuration, as per project best practices:
        - GOOGLE_GENAI_USE_VERTEXAI=True
        - GOOGLE_CLOUD_PROJECT=<your-gcp-project-id>
        - GOOGLE_CLOUD_LOCATION=<your-gcp-region>

        Args:
            model_name: Google embedding model name. Defaults to value from config.yaml.
            output_dimensionality: Desired dimension of embedding output vector. Defaults to value from config.yaml.
            title: Optional title to provide context for the embedding.
            task_type: Type of task for the embedding, e.g., "RETRIEVAL_DOCUMENT".
        """
        super().__init__()

        config = get_config()
        
        if model_name is None:
            model_name = config.get_gemini_embeddings_model()
            logger.debug(f"Using model_name from config: {model_name}")

        is_vertex_ai = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI") == "True"
        
        if is_vertex_ai:
            logger.info("Using Vertex AI. Model name will be used as-is without 'models/' prefix.")
            if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
                raise EnvironmentError(
                    "When 'GOOGLE_GENAI_USE_VERTEXAI' is 'True', the 'GOOGLE_CLOUD_PROJECT' "
                    "environment variable must also be set."
                )
        else:
            if model_name and not model_name.startswith("models/"):
                logger.warning(
                    f"Model name '{model_name}' does not have 'models/' prefix. "
                    f"Prepending it for compatibility with Google AI Studio."
                )
                model_name = f"models/{model_name}"
                logger.debug(f"Updated model name to: {model_name}")
        
        if output_dimensionality is None:
            output_dimensionality = config.get_gemini_embeddings_dimensionality()
            logger.debug(f"Using output_dimensionality from config: {output_dimensionality}")

        self.model_name = model_name
        
        self._gemini_config = {
            "output_dimensionality": output_dimensionality,
            "title": title,
            "task_type": task_type
        }

        # Initialize the genai.Client based on whether we're using Vertex AI or not.
        if is_vertex_ai:
            embedding_location = config.embedding.embedding_location
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
            
            logger.info(f"Initializing Vertex AI client for project '{project_id}' in location '{embedding_location}'.")
            try:
                self._client = genai.Client(
                    vertexai=True,
                    project=project_id,
                    location=embedding_location
                )
                logger.info("Successfully initialized genai.Client for Vertex AI.")
            except Exception as e:
                logger.error(f"Failed to initialize genai.Client for Vertex AI: {e}", exc_info=True)
                logger.error(f"Attempted to call genai.Client with vertexai=True, project='{project_id}', location='{embedding_location}'")
                raise
        else:
            # This is the Google AI Studio path (non-Vertex AI).
            # The client will use the GOOGLE_API_KEY from the environment if available, or ADC.
            logger.info("Initializing genai.Client for Google AI Studio.")
            try:
                self._client = genai.Client()
                logger.info("Successfully initialized genai.Client for Google AI Studio using ADC/API Key.")
            except Exception as e:
                logger.error(f"Failed to initialize genai.Client for Google AI Studio: {e}", exc_info=True)
                raise

    def _get_embedding(
        self, 
        text: str, 
        task_type: Optional[str] = None,
    ) -> List[float]:
        """
        Generate an embedding for a given text input using Google's GenAI API via Vertex AI.
        
        Args:
            text: The text to create an embedding for
            task_type: Optional task type for embedding optimization. Options include:
                      - RETRIEVAL_DOCUMENT: For document content to be retrieved
                      - RETRIEVAL_QUERY: For queries used in retrieval (default)
                      - QUESTION_ANSWERING: For queries formatted as questions
                      - FACT_VERIFICATION: For fact verification
                      - SEMANTIC_SIMILARITY: For text similarity assessment
                      - CLASSIFICATION: For text classification
                      - CLUSTERING: For text clustering
                       
        
        Returns:
            A list of floats representing the embedding vector
        """
        # Prepare EmbedContentConfig parameters
        config_params = {}
        
        # Use function parameter task_type if provided, otherwise use stored task_type
        effective_task_type = task_type if task_type else self._gemini_config.get("task_type")
        
        # Add task_type if specified
        if effective_task_type:
            config_params["task_type"] = effective_task_type
        
        # Always set output dimensionality if specified
        if self._gemini_config.get("output_dimensionality"):
            config_params["output_dimensionality"] = self._gemini_config["output_dimensionality"]
        
        # Add title if provided
        if self._gemini_config.get("title"):
            config_params["title"] = self._gemini_config["title"]
            
        # Create the config object
        embed_config_obj = genai.types.EmbedContentConfig(**config_params)

        try:
            logger.info(f"Requesting Gemini embedding via Vertex AI for model: '{self.model_name}', text: '{text[:70]}...'" )
            # Truncate config for logging
            config_str = str(embed_config_obj)[:100] + "..." if len(str(embed_config_obj)) > 100 else str(embed_config_obj)
            logger.debug(f"Parameters for embed_content: model='{self.model_name}', content='{text[:70]}...', config={config_str}")
            
            # Use the client initialized in __init__ to get the embedding response
            response = self._client.models.embed_content(
                model=self.model_name,
                contents=text,
                config=embed_config_obj
            )
            logger.debug(f"Raw Gemini API response object for text '{text[:60]}...'")
            # Truncate response for logging
            response_str = str(response)[:100] + "..." if len(str(response)) > 100 else str(response)
            logger.debug(f"Truncated response: {response_str}")

            # For Google Gemini via Vertex AI, response has 'embeddings' attribute with a list of ContentEmbedding objects
            # Handle error responses first
            if isinstance(response, dict) and 'error' in response:
                error_msg = response.get('error', {}).get('message', 'Unknown API error')
                error_code = response.get('error', {}).get('code', 'unknown')
                logger.error(f"API error during embedding generation: {error_code} - {error_msg}")
                raise ValueError(f"API error during embedding generation: {error_code} - {error_msg}")
            
            # Handle successful responses in various formats
            if hasattr(response, 'embeddings') and hasattr(response.embeddings[0], 'values'):
                embedding_vector = response.embeddings[0].values
                logger.debug(f"Successfully extracted embedding values from response.embeddings[0].values")
                # Truncate the embedding for display purposes
                truncated = truncate_embedding(embedding_vector)
                logger.info(f"Successfully received embedding. Truncated representation: {truncated}")
                return embedding_vector
                
            # Handle the case when response is a dict with 'embedding' key
            elif isinstance(response, dict) and 'embedding' in response:
                embedding_vector = response['embedding']
                logger.debug(f"Successfully extracted embedding from response['embedding']")
                # Truncate the embedding for display purposes
                truncated = truncate_embedding(embedding_vector)
                logger.info(f"Successfully received embedding. Truncated representation: {truncated}")
                return embedding_vector
                
            # Handle the case when response is a dict with 'embeddings' key
            elif isinstance(response, dict) and 'embeddings' in response:
                embedding_vector = response['embeddings'][0]
                logger.debug(f"Successfully extracted embedding from response['embeddings'][0]")
                # Truncate the embedding for display purposes
                truncated = truncate_embedding(embedding_vector)
                logger.info(f"Successfully received embedding. Truncated representation: {truncated}")
                return embedding_vector
            
            # If we get here, we couldn't extract the embedding
            else:
                logger.warning(f"Could not extract embedding from response: {response}")
                raise ValueError(f"Could not extract embedding from response: {response}")
            

        except genai.errors.APIError as e:
            # Handles errors from the Google API, e.g., NotFoundError, PermissionDeniedError
            error_log_message = (
                f"GoogleAPIError during embedding generation for '{text[:50]}...'. "
                f"Model: {self.model_name}, Type: {type(e).__name__}, Details: {str(e)}"
            )
            logger.error(error_log_message, exc_info=True)
            raise  # Re-raise to ensure failure is propagated
        
        except Exception as e:
            # Handles other unexpected errors (e.g., network, programming errors before API call)
            error_log_message = (
                f"Unexpected error during embedding generation for '{text[:50]}...'. "
                f"Model: {self.model_name}, Type: {type(e).__name__}, Details: {str(e)}"
            )
            logger.error(error_log_message, exc_info=True)
            raise # Re-raise to ensure failure is propagated

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
