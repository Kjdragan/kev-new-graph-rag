# src/graph_extraction/extractor.py
import uuid
import asyncio
import logging # Added for logging
from typing import List, Type, Dict, Any
from pydantic import BaseModel

from graphiti_core import Graphiti
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.llm_client import LLMConfig # LLMConfig is correctly exported
from graphiti_core.nodes import EpisodeType # For add_episode source
# from graphiti_core.embedder import EmbedderClient # Not used in this version

from src.ontology_templates.generic_ontology import BaseNode, BaseRelationship
from utils.config import get_config

# Setup logger for this module
logger = logging.getLogger(__name__) # Added

class GraphExtractor:
    """
    Orchestrates the knowledge graph extraction process using graphiti-core.
    It takes text and an ontology definition, and returns an extracted graph.
    """
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_pass: str, gemini_api_key: str):
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
        
        llm_config_for_graphiti = LLMConfig(
            model=self.config.gemini_model_name_graph_extraction, 
            api_key=gemini_api_key
        )
        self.graphiti_llm = GeminiClient(config=llm_config_for_graphiti)
        logger.info(f"Graphiti GeminiClient initialized with model: {self.config.gemini_model_name_graph_extraction}") # Added

        self.graphiti_instance = Graphiti(
            uri=neo4j_uri,
            user=neo4j_user,
            password=neo4j_pass,
            llm_client=self.graphiti_llm
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
            add_episode_result = await self.graphiti_instance.add_episode(
                name=episode_name,
                content=text_content,
                source=EpisodeType.text, 
                source_description=episode_source_description,
                group_id=group_id,
                entity_types=entity_types_map,
                edge_types=edge_types_map,
            )
            logger.info(f"Successfully extracted data for episode: {episode_name}. Nodes: {len(add_episode_result.nodes)}, Edges: {len(add_episode_result.edges)}") # Added
            return add_episode_result.model_dump()
        except Exception as e: # Added error handling
            logger.error(f"Error during graphiti add_episode for episode {episode_name}: {e}", exc_info=True)
            raise # Re-raise the exception after logging

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

