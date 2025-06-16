"""
Test script for the hybrid Graphiti search implementation.
Verifies that CustomGeminiEmbedding works with Graphiti's search functions.
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from src.graph_querying.graphiti_native_search import GraphitiNativeSearcher

async def test_hybrid_search():
    """Test the hybrid search approach with CustomGeminiEmbedding + Graphiti search."""
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    
    try:
        logger.info("=== Testing Hybrid Graphiti Search ===")
        
        # Initialize the search system
        logger.info("Initializing GraphitiNativeSearcher with hybrid approach...")
        async with GraphitiNativeSearcher() as search_system:
            # Test queries
            test_queries = [
                "artificial intelligence research",
                "machine learning algorithms",
                "data science methodologies"
            ]
            
            for query in test_queries:
                logger.info(f"\n--- Testing Query: '{query}' ---")
                
                try:
                    # Test hybrid search
                    results = await search_system.hybrid_search(query, limit=5)
                    
                    logger.info(f"✅ Hybrid search successful! Found {len(results)} results")
                    
                    # Display results summary
                    if results:
                        logger.info("Top results:")
                        formatted_results = search_system.format_search_results(results)
                        for i, result in enumerate(formatted_results[:3], 1):
                            logger.info(f"  {i}. {result['fact']}")
                    else:
                        logger.warning("No results found for this query")
                        
                except Exception as e:
                    logger.error(f"❌ Hybrid search failed for query '{query}': {str(e)}")
                    logger.exception("Exception details:")
            
            # Test entity-focused search
            logger.info(f"\n--- Testing Entity-Focused Search ---")
            try:
                entity_results = await search_system.entity_focused_search(
                    query="research methodology",
                    entity_name="artificial intelligence",
                    limit=3
                )
                
                logger.info(f"✅ Entity-focused search successful! Found {len(entity_results)} results")
                
            except Exception as e:
                logger.error(f"❌ Entity-focused search failed: {str(e)}")
                logger.exception("Exception details:")
        
        logger.info("✅ Test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed during initialization: {str(e)}")
        logger.exception("Exception details:")

if __name__ == "__main__":
    asyncio.run(test_hybrid_search())
