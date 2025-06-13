# src/graph_extraction/extractor.py
import uuid
import asyncio
import logging # Added for logging
from typing import List, Type, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from graphiti_core import Graphiti
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.llm_client import LLMConfig # LLMConfig is correctly exported
from graphiti_core.nodes import EpisodeType # For add_episode source
from graphiti_core.embedder import EmbedderClient # Import EmbedderClient
from graphiti_core.embedder.gemini import GeminiEmbedderConfig # Import Gemini embedder config

# Import our custom BatchSizeOneGeminiEmbedder instead of the standard GeminiEmbedder
from src.graph_extraction.gemini_embedder import BatchSizeOneGeminiEmbedder
from src.ontology_templates.generic_ontology import BaseNode, BaseRelationship
from utils.config import get_config

# Setup logger for this module
logger = logging.getLogger(__name__) # Added

import inspect
from loguru import logger

class GraphExtractor:
    """
    Orchestrates the knowledge graph extraction process using graphiti-core.
    It takes text and an ontology definition, and returns an extracted graph.
    """
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_pass: str, gemini_api_key: str = None):
        """
        Initializes the GraphExtractor.

        Args:
            neo4j_uri: URI for the Neo4j instance.
            neo4j_user: Username for Neo4j.
            neo4j_pass: Password for Neo4j.
            gemini_api_key: API key for Google Gemini.
        """
        logger.info("Initializing GraphExtractor...") # Added
        self.config = get_config()

        # Use the pro model from config, or fall back to a reasonable default
        # When api_key is None, google-genai will automatically use Application Default Credentials (ADC)
        # that have been set up with 'gcloud auth application-default login'
        llm_config_for_graphiti = LLMConfig(
            model=self.config.get("gemini.models.pro.model_id", "gemini-2.5-pro-preview-06-05"),
            api_key=None,  # Setting to None to force ADC usage
            temperature=0.2,  # Lower temperature for more consistent results
            max_tokens=16000   # Ensure sufficient token budget for complex extractions
        )

        # Create a GeminiClient that will use ADC authentication
        self.graphiti_llm = GeminiClient(config=llm_config_for_graphiti)

        # Override the client to use ADC authentication instead of API key
        # This is necessary because graphiti-core's GeminiClient doesn't support ADC natively
        from google import genai
        self.graphiti_llm.client = genai.Client()  # No API key = use ADC
        logger.info(f"Graphiti GeminiClient initialized with model: {llm_config_for_graphiti.model}") # Added

        # Create a BatchSizeOneGeminiEmbedder that will use ADC authentication
        # Get the embedding model ID from config, or use a default
        embedding_model = self.config.get("gemini.models.embedding.model_id", "gemini-embedding-001")
        embedding_dim = self.config.get("gemini.models.embedding.dimensions", 1536)

        # Create embedder config with no API key to force ADC usage
        embedder_config = GeminiEmbedderConfig(
            embedding_model=embedding_model,
            embedding_dim=embedding_dim,
            api_key=None  # Setting to None to force ADC usage
        )

        # Initialize our custom BatchSizeOneGeminiEmbedder with our config
        # This version handles the batch size=1 constraint of the Gemini embedding API
        self.graphiti_embedder = BatchSizeOneGeminiEmbedder(config=embedder_config)

        # Override the client to use ADC authentication
        self.graphiti_embedder.client = genai.Client()  # No API key = use ADC
        logger.info(f"BatchSizeOneGeminiEmbedder initialized with model: {embedding_model}, dimensions: {embedding_dim}")

        self.graphiti_instance = Graphiti(
            uri=neo4j_uri,
            user=neo4j_user,
            password=neo4j_pass,
            llm_client=self.graphiti_llm,
            embedder=self.graphiti_embedder  # Pass our BatchSizeOneGeminiEmbedder instance
        )
        logger.info(f"Graphiti instance initialized for Neo4j URI: {neo4j_uri}") # Added

        # Note: `build_indices_and_constraints` is an async method.
        # It's best to run this once during application setup, not in __init__ if __init__ is sync.
        # For example, create an async `setup` method for the extractor or run it in the main app startup.
        # try:
        #     asyncio.run(self.graphiti_instance.build_indices_and_constraints())
        #     logger.info("Successfully built Graphiti indices and constraints.")
        # except Exception as e:
        #     logger.warning(f"Could not build Graphiti indices/constraints during init: {e}")


    async def extract(
        self,
        text_content: str,
        ontology_nodes: List[Type[BaseNode]],
        ontology_edges: List[Type[BaseRelationship]],
        group_id: str = "default_group",
        episode_name_prefix: str = "doc_extract"
    ) -> Dict[str, Any]:
        """
        Extracts entities and relationships from text content based on the provided ontology.

        Args:
            text_content: The input text to extract from.
            ontology_nodes: A list of Pydantic models representing the node types for extraction.
            ontology_edges: A list of Pydantic models representing the relationship types for extraction.
            group_id: An identifier for the data group in graphiti.
            episode_name_prefix: Prefix for the generated episode name.

        Returns:
            A dictionary representing the results from graphiti's add_episode.
        """
        logger.info(f"Starting graph extraction for group_id: {group_id} with prefix: {episode_name_prefix}") # Added
        entity_types_map: Dict[str, Type[BaseModel]] = {node_model.__name__: node_model for node_model in ontology_nodes}
        edge_types_map: Dict[str, Type[BaseModel]] = {edge_model.__name__: edge_model for edge_model in ontology_edges}
        logger.debug(f"Entity types for extraction: {list(entity_types_map.keys())}") # Added
        logger.debug(f"Edge types for extraction: {list(edge_types_map.keys())}") # Added

        episode_name = f"{episode_name_prefix}_{uuid.uuid4()}"
        episode_source_description = "Document processed for KG extraction via GraphExtractor"

        try:
            logger.info(f"Calling graphiti_instance.add_episode for episode: {episode_name}") # Added
            # Prepare arguments for add_episode from the provided ontology
            # Based on the signature, entity_types should be a dict mapping names to models
            entity_types_dict: Dict[str, Type[BaseModel]] = {}

            # Add node types to entity_types_dict
            for node_model in ontology_nodes:
                entity_types_dict[node_model.__name__] = node_model

            # Add edge types to entity_types_dict
            for edge_model in ontology_edges:
                entity_types_dict[edge_model.__name__] = edge_model

            # Store these on self to ensure they're available during add_episode execution
            self.ontology_entity_types = ontology_nodes
            self.ontology_edge_types = ontology_edges
            self.ontology_edge_type_map = {edge_model.__name__: edge_model for edge_model in ontology_edges}

            logger.info(f"Calling add_episode with entity_types: {list(entity_types_dict.keys())}")

            try:
                sig = inspect.signature(self.graphiti_instance.add_episode)
                logger.info(f"Signature of loaded graphiti_instance.add_episode: {sig}")
            except Exception as e:
                logger.error(f"Could not get signature of graphiti_instance.add_episode: {e}")
                logger.info(f"Dir of graphiti_instance: {dir(self.graphiti_instance)}")

            # Add retry logic for NoneType errors
            max_retries = 1  # Try once more after initial failure
            retry_count = 0
            last_error = None

            while retry_count <= max_retries:
                try:
                    add_episode_result = await self.graphiti_instance.add_episode(
                        name=episode_name,
                        episode_body=text_content,
                        source_description=episode_source_description,
                        reference_time=datetime.utcnow(),
                        entity_types=entity_types_dict,
                        group_id=group_id
                    )
                    logger.info(f"Successfully extracted data for episode: {episode_name}. Nodes: {len(add_episode_result.nodes)}, Edges: {len(add_episode_result.edges)}") # Added
                    return add_episode_result.model_dump()
                except Exception as e:
                    last_error = e
                    error_msg = str(e)

                    # Check if this is the NoneType JSON parsing error
                    if "the JSON object must be str, bytes or bytearray, not NoneType" in error_msg:
                        if retry_count < max_retries:
                            retry_count += 1
                            logger.warning(f"Encountered NoneType response error, retrying ({retry_count}/{max_retries})...")
                            await asyncio.sleep(2)  # Wait a bit before retrying
                            continue
                        else:
                            logger.error(f"Failed to parse structured response after {max_retries} retries")

                    # If we get here, either it's not a NoneType error or we've exhausted retries
                    break

            # If we get here, all retries failed or it was a different error
            # Log error message without full exception details that might contain embedding vectors
            error_msg = str(last_error)
            if len(error_msg) > 500:  # Truncate long error messages that might contain embeddings
                error_msg = error_msg[:500] + "... [truncated]"
            logger.error(f"Error during graphiti add_episode for episode {episode_name}: {error_msg}")
            # Log stack trace separately without the full exception object
            logger.error("Stack trace:", exc_info=True)
            raise last_error  # Re-raise the last exception after logging
        except Exception as e: # This catch block is now redundant as we handle errors in the retry loop
            # This code should never be reached due to the retry logic above
            # But keeping it as a fallback just in case
            error_msg = str(e)
            if len(error_msg) > 500:  # Truncate long error messages that might contain embeddings
                error_msg = error_msg[:500] + "... [truncated]"
            logger.error(f"Unexpected error path in extract method for episode {episode_name}: {error_msg}")
            logger.error("Stack trace:", exc_info=True)
            raise  # Re-raise the exception after logging

    async def close(self):
        """Closes the Graphiti Neo4j driver connection."""
        logger.info("Closing Graphiti Neo4j driver connection.") # Added
        await self.graphiti_instance.close()
        logger.info("Graphiti Neo4j driver connection closed.") # Added

# Example usage (for testing, typically not here):
# async def main():
#     # Load from .env or config
#     NEO4J_URI = "bolt://localhost:7687"
#     NEO4J_USER = "neo4j"
#     NEO4J_PASSWORD = "password"
#     GEMINI_API_KEY = "your_gemini_api_key"
#     # Ensure logging is configured for the example to show output
#     # logging.basicConfig(level=logging.INFO)

#     extractor = GraphExtractor(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, GEMINI_API_KEY)

#     # Example ontology (replace with actual loaded ontology)
#     from src.ontology_templates.financial_report_ontology import NODE_TYPES, RELATIONSHIP_TYPES

#     sample_text = "Acme Corp announced record profits for Q4 2023. John Doe, CEO, was pleased."

#     try:
#         extracted_data = await extractor.extract(sample_text, NODE_TYPES, RELATIONSHIP_TYPES)
#         logger.info(f"Extraction successful: {extracted_data}")
#     except Exception as e:
#         logger.error(f"Extraction failed: {e}", exc_info=True)
#     finally:
#         await extractor.close()

# if __name__ == "__main__":
#     # To run the example, ensure your environment is set up (Neo4j, Gemini API key)
#     # and uncomment the logging.basicConfig line above.
#     asyncio.run(main())

