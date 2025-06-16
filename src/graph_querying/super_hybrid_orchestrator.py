# src/graph_querying/super_hybrid_orchestrator.py
# Orchestrates queries across ChromaDB and Neo4j (Graphiti) for a super-hybrid search.

import asyncio
from typing import Dict, Any
from loguru import logger

from utils.config_models import ChromaDBConfig
from utils.chroma_ingester import ChromaIngester
from utils.embedding import CustomGeminiEmbedding
from src.graph_querying.graphiti_native_search import GraphitiNativeSearcher

class SuperHybridOrchestrator:
    """
    Orchestrates hybrid search queries across a vector store (ChromaDB)
    and a graph database (Neo4j via Graphiti).
    """

    def __init__(self):
        """Initializes the orchestrator and its underlying clients."""
        logger.info("Initializing SuperHybridOrchestrator...")
        try:
            # Load only the configuration needed for this orchestrator
            chroma_config = ChromaDBConfig()
            embedding_model = CustomGeminiEmbedding()
            
            # Initialize ChromaDB client via ChromaIngester
            self.chroma_ingester = ChromaIngester(chroma_config, embedding_model)
            
            # Initialize Graphiti searcher
            self.graphiti_searcher = GraphitiNativeSearcher()
            logger.info("SuperHybridOrchestrator initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize SuperHybridOrchestrator: {e}", exc_info=True)
            raise

    async def search(self, query: str, n_results_chroma: int = 5, n_results_graph: int = 10) -> Dict[str, Any]:
        """
        Performs a concurrent search on both ChromaDB and the Knowledge Graph.

        Args:
            query: The user's search query.
            n_results_chroma: Number of results to fetch from ChromaDB.
            n_results_graph: Number of results to fetch from the graph.

        Returns:
            A dictionary containing the combined search results.
        """
        logger.info(f"Performing super hybrid search for query: '{query}'")

        # Define the two concurrent search tasks
        chroma_task = asyncio.to_thread(
            self.chroma_ingester.search, 
            query=query, 
            n_results=n_results_chroma
        )
        
        graph_task = self.graphiti_searcher.advanced_search_with_recipe(
            query=query,
            recipe_name='combined_hybrid',
            num_results=n_results_graph
        )

        # Run tasks concurrently and gather results
        try:
            chroma_results, graph_results = await asyncio.gather(chroma_task, graph_task)
            logger.info(f"ChromaDB returned {len(chroma_results.get('documents', [[]])[0])} results.")
            logger.info(f"Graphiti returned {graph_results.get('num_nodes', 0)} nodes and {graph_results.get('num_edges', 0)} edges.")

            return {
                "query": query,
                "chroma_context": chroma_results,
                "graph_context": graph_results
            }
        except Exception as e:
            logger.error(f"Error during concurrent search: {e}", exc_info=True)
            return {
                "error": str(e),
                "chroma_context": {},
                "graph_context": {}
            }

    async def close(self):
        """Closes any open connections."""
        # GraphitiNativeSearcher uses an async context manager, so no explicit close is needed here
        # for the instance variable. If it were initialized differently, we'd close it here.
        logger.info("SuperHybridOrchestrator connections managed by context handlers.")
        pass
