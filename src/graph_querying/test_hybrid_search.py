#!/usr/bin/env python3
"""
Test script for Graphiti native search integration with custom 1536-dimensional embeddings.
This verifies that the hybrid search pipeline works end-to-end.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src to path for imports

from src.graph_querying.graphiti_native_search import GraphitiNativeSearcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_hybrid_search():
    """Test the hybrid search functionality with various queries."""
    
    test_queries = [
        "What is artificial intelligence?",
        "Who are the key researchers in AI?",
        "Tell me about machine learning frameworks",
        "What are the latest developments in generative AI?",
        "How does natural language processing work?"
    ]
    
    logger.info("Starting Graphiti native search tests...")
    
    try:
        async with GraphitiNativeSearcher() as searcher:
            logger.info("Successfully initialized GraphitiNativeSearcher")
            
            for i, query in enumerate(test_queries, 1):
                logger.info(f"\n{'='*80}")
                logger.info(f"TEST {i}: {query}")
                logger.info(f"{'='*80}")
                
                try:
                    # Test 1: Standard hybrid search
                    logger.info("\n--- Standard Hybrid Search ---")
                    hybrid_results = await searcher.hybrid_search(query, num_results=5)
                    
                    logger.info(f"Query: {hybrid_results['query']}")
                    logger.info(f"Custom embedding dimensionality: {hybrid_results['custom_embedding_dim']}")
                    logger.info(f"Number of results: {hybrid_results['num_results']}")
                    
                    if hybrid_results['results']:
                        logger.info("Top results:")
                        for j, result in enumerate(hybrid_results['results'][:3], 1):
                            logger.info(f"  {j}. {result['fact']}")
                            logger.info(f"     UUID: {result['uuid']}")
                            logger.info(f"     Valid: {result['valid_at']} to {result['invalid_at']}")
                    else:
                        logger.info("No results found for hybrid search")
                    
                    # Test 2: Advanced search with recipe
                    logger.info("\n--- Advanced Search with Recipe ---")
                    advanced_results = await searcher.advanced_search_with_recipe(
                        query, 
                        recipe_name="combined_hybrid", 
                        num_results=3
                    )
                    
                    logger.info(f"Recipe: {advanced_results['recipe']}")
                    logger.info(f"Custom embedding dimensionality: {advanced_results['custom_embedding_dim']}")
                    logger.info(f"Edges found: {advanced_results['num_edges']}")
                    logger.info(f"Nodes found: {advanced_results['num_nodes']}")
                    
                    if advanced_results['edges']:
                        logger.info("Top edge results:")
                        for j, edge in enumerate(advanced_results['edges'][:2], 1):
                            logger.info(f"  {j}. {edge['fact']}")
                    
                    if advanced_results['nodes']:
                        logger.info("Top node results:")
                        for j, node in enumerate(advanced_results['nodes'][:2], 1):
                            logger.info(f"  {j}. {node['name']}: {node['summary']}")
                    
                    # Test 3: Entity-focused search (if we have results from previous searches)
                    if advanced_results['nodes']:
                        logger.info("\n--- Entity-Focused Search ---")
                        center_node_uuid = advanced_results['nodes'][0]['uuid']
                        
                        entity_results = await searcher.entity_focused_search(
                            query, 
                            center_node_uuid=center_node_uuid, 
                            num_results=3
                        )
                        
                        logger.info(f"Center node UUID: {entity_results['center_node_uuid']}")
                        logger.info(f"Entity-focused results: {entity_results['num_results']}")
                        
                        if entity_results['results']:
                            logger.info("Entity-focused facts:")
                            for j, result in enumerate(entity_results['results'], 1):
                                logger.info(f"  {j}. {result['fact']}")
                    
                except Exception as e:
                    logger.error(f"Error testing query '{query}': {str(e)}")
                    continue
                
                # Add a small delay between queries
                await asyncio.sleep(1)
    
    except Exception as e:
        logger.error(f"Failed to initialize or run tests: {str(e)}")
        raise

async def test_embedding_compatibility():
    """Test that our custom embeddings are working correctly."""
    
    logger.info("\n" + "="*80)
    logger.info("EMBEDDING COMPATIBILITY TEST")
    logger.info("="*80)
    
    try:
        async with GraphitiNativeSearcher() as searcher:
            # Test embedding generation using the same method as ingestion pipeline
            test_text = "This is a test query for embedding generation"
            embedding = searcher.embedding_client._get_text_embedding(test_text)
            
            logger.info(f"Test text: {test_text}")
            logger.info(f"Generated embedding dimensionality: {len(embedding)}")
            logger.info(f"Expected dimensionality: 1536")
            logger.info(f"Embedding compatibility: {'✓ PASS' if len(embedding) == 1536 else '✗ FAIL'}")
            
            if len(embedding) != 1536:
                logger.error("Embedding dimensionality mismatch! This will cause Neo4j vector search errors.")
                return False
            
            logger.info("Embedding test completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Embedding compatibility test failed: {str(e)}")
        return False

async def main():
    """Main test runner."""
    
    logger.info("Starting Graphiti hybrid search integration tests...")
    
    # Test 1: Embedding compatibility
    embedding_success = await test_embedding_compatibility()
    
    if not embedding_success:
        logger.error("Embedding compatibility test failed. Skipping search tests.")
        return
    
    # Test 2: Search functionality
    await test_hybrid_search()
    
    logger.info("\n" + "="*80)
    logger.info("ALL TESTS COMPLETED")
    logger.info("="*80)

if __name__ == "__main__":
    asyncio.run(main())
