"""
Native Graphiti search implementation using built-in capabilities.
This approach leverages Graphiti's hybrid search, reranking, and search recipes
instead of manually crafting Cypher queries.
"""
import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
import dotenv
from loguru import logger

from graphiti_core import Graphiti
from graphiti_core.search.search import search as _internal_core_search
from graphiti_core.search.search_config import SearchConfig, EdgeSearchConfig, EdgeSearchMethod, EdgeReranker
from graphiti_core.search.search_filters import SearchFilters
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.search.search_config_recipes import (
    EDGE_HYBRID_SEARCH_RRF,
    EDGE_HYBRID_SEARCH_MMR,
    EDGE_HYBRID_SEARCH_NODE_DISTANCE,
    EDGE_HYBRID_SEARCH_EPISODE_MENTIONS,
    EDGE_HYBRID_SEARCH_CROSS_ENCODER,
    COMBINED_HYBRID_SEARCH_RRF,
    COMBINED_HYBRID_SEARCH_MMR,
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER
)
from graphiti_core.search.search_filters import SearchFilters
from utils.embedding import CustomGeminiEmbedding
from utils.config import Config
from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EntityNode


class GraphitiNativeSearcher:
    """
    Native Graphiti search implementation that uses Graphiti's built-in
    search capabilities instead of manual Cypher generation.
    """
    
    def __init__(self):
        dotenv.load_dotenv()
        
        # Neo4j connection parameters
        self.neo4j_uri = os.getenv('NEO4J_URI')
        self.neo4j_user = os.getenv('NEO4J_USERNAME')
        self.neo4j_password = os.getenv('NEO4J_PASSWORD')
        
        # Vertex AI / ADC configuration
        self.google_cloud_project = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.google_cloud_location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        if not all([self.neo4j_uri, self.neo4j_user, self.neo4j_password]):
            raise ValueError("NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD must be set")
        
        if not self.google_cloud_project:
            raise ValueError("GOOGLE_CLOUD_PROJECT must be set for Vertex AI authentication")
        
        self.graphiti = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Configure environment for Vertex AI ADC authentication
        os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'True'
        os.environ['GOOGLE_CLOUD_PROJECT'] = self.google_cloud_project
        os.environ['GOOGLE_CLOUD_LOCATION'] = self.google_cloud_location
        
        # Configure Gemini LLM client for Graphiti operations (not for embeddings)
        llm_config = LLMConfig(
            model="gemini-2.0-flash-exp",  # Use latest Gemini model
            api_key=None  # Uses ADC via GOOGLE_GENAI_USE_VERTEXAI=true
        )
        llm_client = GeminiClient(config=llm_config)
        
        # Initialize custom embedding client (same as used in ingestion)
        self.embedding_client = CustomGeminiEmbedding(
            model_name="gemini-embedding-001",  # Use same model as ingestion
            output_dimensionality=1536  # Match existing database dimensions
        )
        
        # Initialize Gemini embedder for Graphiti
        gemini_embedder = GeminiEmbedder(
            config=GeminiEmbedderConfig(
                embedding_model="gemini-embedding-001",
                embedding_dim=1536,  # Match Neo4j database dimensions
                # No API key needed when using Vertex AI
            )
        )
        
        # Initialize Graphiti client with Gemini embedder
        self.graphiti = Graphiti(
            uri=self.neo4j_uri,
            user=self.neo4j_user,
            password=self.neo4j_password,
            llm_client=llm_client,
            embedder=gemini_embedder
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.graphiti:
            await self.graphiti.close()
    
    async def hybrid_search(
        self, 
        query: str, 
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Perform hybrid search using Graphiti's built-in search with custom embeddings.
        
        Args:
            query: Search query string
            num_results: Number of results to return
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            logger.info(f"Starting hybrid search for query: '{query}'")
            
            # Generate custom 1536-dimensional embedding for the query
            query_embedding = self.embedding_client._get_query_embedding(query)
            logger.info(f"Generated {len(query_embedding)}-dimensional query embedding")
            
            # Prepare search configuration for internal search
            core_clients = self.graphiti.clients
            
            # Create a hybrid search config (vector + keyword search)
            edge_config = EdgeSearchConfig(
                search_methods=[EdgeSearchMethod.cosine_similarity, EdgeSearchMethod.bm25],
                reranker=EdgeReranker.rrf
            )
            
            search_config = SearchConfig(
                edge_config=edge_config,
                limit=num_results
            )

            # Use Graphiti's internal search method with custom query vector
            search_results_obj = await _internal_core_search(
                clients=core_clients,
                query=query,
                query_vector=query_embedding,
                group_ids=None,  # Assuming no specific group_ids for now
                config=search_config,
                search_filter=SearchFilters() # Assuming default filters
            )
            search_results = search_results_obj.edges # Extract edges from SearchResults object
            
            logger.info(f"Retrieved {len(search_results)} search results from internal search")
            
            # Process and format results
            formatted_results = []
            for edge in search_results:
                result = {
                    'uuid': edge.uuid,
                    'fact': edge.fact,
                    'source_node_uuid': edge.source_node_uuid,
                    'target_node_uuid': edge.target_node_uuid,
                    'valid_at': str(edge.valid_at) if edge.valid_at else None,
                    'invalid_at': str(edge.invalid_at) if edge.invalid_at else 'Present',
                    'created_at': str(edge.created_at) if edge.created_at else None
                }
                formatted_results.append(result)
            
            return {
                'query': query,
                'num_results': len(formatted_results),
                'custom_embedding_dim': len(query_embedding),
                'results': formatted_results
            }
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            raise
    
    async def entity_focused_search(
        self, 
        query: str, 
        center_node_uuid: Optional[str] = None,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Perform entity-focused search using graph distance reranking.
        
        Args:
            query: Search query string
            center_node_uuid: UUID of center node for distance-based reranking
            num_results: Number of results to return
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            logger.info(f"Starting entity-focused search for query: '{query}'")
            if center_node_uuid:
                logger.info(f"Using center node UUID: {center_node_uuid}")
            
            # Generate custom 1536-dimensional embedding for the query
            query_embedding = self.embedding_client._get_query_embedding(query)
            logger.info(f"Generated {len(query_embedding)}-dimensional query embedding")
            
            # Use Graphiti's search method with center node for reranking
            search_results = await self.graphiti.search(
                query=query,
                query_vector=query_embedding,
                center_node_uuid=center_node_uuid,
                num_results=num_results,
                search_filter=SearchFilters()
            )
            
            logger.info(f"Retrieved {len(search_results)} entity-focused search results")
            
            # Process and format results
            formatted_results = []
            for edge in search_results:
                result = {
                    'uuid': edge.uuid,
                    'fact': edge.fact,
                    'source_node_uuid': edge.source_node_uuid,
                    'target_node_uuid': edge.target_node_uuid,
                    'valid_at': str(edge.valid_at) if edge.valid_at else None,
                    'invalid_at': str(edge.invalid_at) if edge.invalid_at else 'Present',
                    'created_at': str(edge.created_at) if edge.created_at else None
                }
                formatted_results.append(result)
            
            return {
                'query': query,
                'center_node_uuid': center_node_uuid,
                'num_results': len(formatted_results),
                'custom_embedding_dim': len(query_embedding),
                'results': formatted_results
            }
            
        except Exception as e:
            logger.error(f"Error in entity-focused search: {str(e)}")
            raise
    
    async def advanced_search_with_recipe(
        self, 
        query: str, 
        recipe_name: str = "edge_hybrid",
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Perform advanced search using Graphiti's search_ method with specific recipes.
        
        Args:
            query: Search query string
            recipe_name: Name of search recipe to use ('edge_hybrid', 'node_hybrid', 'combined_hybrid')
            num_results: Number of results to return
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            logger.info(f"Starting advanced search with recipe '{recipe_name}' for query: '{query}'")
            
            # Generate custom 1536-dimensional embedding for the query
            query_embedding = self.embedding_client._get_query_embedding(query)
            logger.info(f"Generated {len(query_embedding)}-dimensional query embedding")
            
            # Select search configuration based on recipe name
            if recipe_name == "edge_hybrid":
                config = EDGE_HYBRID_SEARCH_RRF
            elif recipe_name == "node_hybrid":
                logger.warning(f"Unknown recipe '{recipe_name}', using default combined hybrid")
                config = COMBINED_HYBRID_SEARCH_RRF
            elif recipe_name == "combined_hybrid":
                config = COMBINED_HYBRID_SEARCH_RRF
            else:
                logger.warning(f"Unknown recipe '{recipe_name}', using default combined hybrid")
                config = COMBINED_HYBRID_SEARCH_RRF
            
            # Adjust the limit for the selected config
            config.limit = num_results
            
            # NOTE: The public Graphiti.search_() method does not accept query_vector parameter
            # Unlike the internal _internal_core_search function, we can't inject pre-computed embeddings
            # This means recipe-based search will use Graphiti's built-in embedding generation
            # which may not match our custom embedding dimensions
            search_results = await self.graphiti.search_(
                query=query,
                config=config,
                search_filter=SearchFilters()
            )
            
            logger.info(f"Advanced search returned {len(search_results.edges)} edges and {len(search_results.nodes)} nodes")
            
            # Format edge results
            formatted_edges = []
            for edge in search_results.edges:
                result = {
                    'uuid': edge.uuid,
                    'fact': edge.fact,
                    'source_node_uuid': edge.source_node_uuid,
                    'target_node_uuid': edge.target_node_uuid,
                    'valid_at': str(edge.valid_at) if edge.valid_at else None,
                    'invalid_at': str(edge.invalid_at) if edge.invalid_at else 'Present',
                    'created_at': str(edge.created_at) if edge.created_at else None
                }
                formatted_edges.append(result)
            
            # Format node results
            formatted_nodes = []
            for node in search_results.nodes:
                result = {
                    'uuid': node.uuid,
                    'name': node.name,
                    'summary': node.summary,
                    'labels': node.labels,
                    'created_at': str(node.created_at) if node.created_at else None
                }
                formatted_nodes.append(result)
            
            return {
                'query': query,
                'recipe': recipe_name,
                'custom_embedding_dim': len(query_embedding),
                'edges': formatted_edges,
                'nodes': formatted_nodes,
                'num_edges': len(formatted_edges),
                'num_nodes': len(formatted_nodes)
            }
            
        except Exception as e:
            logger.error(f"Error in advanced search with recipe: {str(e)}")
            raise
    
    async def main(self):
        """Example usage demonstrating native Graphiti search capabilities."""
        
        test_queries = [
            "Who created GPT-4?",
            "What is artificial intelligence?",
            "Tell me about OpenAI",
        ]
        
        async with self:
            for query in test_queries:
                print(f"\n{'='*60}")
                print(f"Query: {query}")
                print(f"{'='*60}")
                
                # 1. Standard hybrid search
                print("\n1. Standard Hybrid Search:")
                hybrid_results = await self.hybrid_search(query, num_results=3)
                print(f"  Retrieved {len(hybrid_results['results'])} results")
                
                # 2. Entity-focused search (if query mentions specific entities)
                if any(entity in query.lower() for entity in ['gpt-4', 'openai', 'chatgpt']):
                    print("\n2. Entity-focused Search:")
                    entity_name = 'OpenAI' if 'gpt-4' in query.lower() or 'openai' in query.lower() else query.split()[0]
                    entity_results = await self.entity_focused_search(query, entity_name, num_results=3)
                    print(f"  Retrieved {len(entity_results['results'])} entity-focused results")
                
                # 3. Advanced search with different recipe
                print("\n3. Advanced Search (Combined Hybrid):")
                advanced_results = await self.advanced_search_with_recipe(
                    query, 
                    recipe_name="combined_hybrid", 
                    num_results=2
                )
                print(f"  Retrieved {len(advanced_results['edges'])} edges and {len(advanced_results['nodes'])} nodes")


if __name__ == "__main__":
    asyncio.run(GraphitiNativeSearcher().main())
