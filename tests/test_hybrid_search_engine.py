"""
Test module for HybridSearchEngine

This module contains comprehensive tests for the HybridSearchEngine class
that combines knowledge graph traversal with vector similarity search.
"""
import os
import sys
import unittest
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit

# Add the parent directory to sys.path to enable imports from project modules
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.hybrid_search_engine import HybridSearchEngine
from utils.config import get_config


class TestHybridSearchEngine(unittest.TestCase):
    """Unit tests for HybridSearchEngine using mocks for all external dependencies"""
    """Test cases for HybridSearchEngine"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock Neo4j driver
        self.mock_driver = MagicMock()
        self.mock_session = MagicMock()
        self.mock_driver.session.return_value.__enter__.return_value = self.mock_session
        
        # Mock embedding model
        self.mock_embedding_model = MagicMock()
        self.mock_embedding_model.get_embedding.return_value = [0.1, 0.2, 0.3]
        
        # Mock LLM (Gemini)
        self.mock_llm = MagicMock()
        self.mock_llm.generate_content.return_value.text = "Generated response"
        
        # Create HybridSearchEngine instance with mocks
        self.engine = HybridSearchEngine(
            neo4j_driver=self.mock_driver,
            embedding_model=self.mock_embedding_model,
            llm=self.mock_llm,
            config={"thinking_budget": 1024}
        )
        
        # Sample test data
        self.test_query = "Who is Kevin Smith and where does he work?"
        self.test_entities = [
            {"entity": "Kevin Smith", "type": "Person"},
            {"entity": "work", "type": "Activity"}
        ]
        self.test_relationships = ["employment"]
        
        # Mock Neo4j query results - Raw format from Neo4j
        # Create a proper relationship mock that behaves like a dictionary
        class MockRelationship:
            def __init__(self, rel_type, **props):
                self.rel_type = rel_type
                self.props = props
                # Set class name to match relationship type for type(r).__name__
                self.__class__.__name__ = rel_type
            
            def __iter__(self):
                # This is needed for dict(r) to work
                return iter(self.props.items())
                
            def items(self):
                return self.props.items()
                
            def __getitem__(self, key):
                return self.props[key]
        
        # Create a mock relationship for our test
        mock_rel = MockRelationship("WORKS_AT", since="2020")
        
        self.mock_neo4j_raw_results = [
            {
                "n1": {"name": "Kevin Smith", "entity_type": "Person"}, 
                "r": mock_rel, 
                "n2": {"name": "Acme Technologies", "entity_type": "Organization"}
            }
        ]
        
        # Expected processed results after _query_knowledge_graph transforms them
        self.mock_graph_results = [
            {
                "source": {"name": "Kevin Smith", "type": "Person", "props": {}},
                "relationship": {"type": "WORKS_AT", "props": {}},
                "target": {"name": "Acme Technologies", "type": "Organization", "props": {}}
            }
        ]
        
        # Mock vector search results
        self.mock_vector_results = [
            {"text": "Kevin Smith is a software engineer at Acme Technologies", "score": 0.95},
            {"text": "Acme Technologies is located in San Francisco", "score": 0.82}
        ]

    def test_extract_query_structure(self):
        """Test entity and relationship extraction from query."""
        # Configure mock LLM to return structured output
        mock_result = MagicMock()
        mock_result.candidates = [MagicMock()]
        mock_result.candidates[0].content.function_call = MagicMock()
        mock_result.candidates[0].content.function_call.args = {
            "entities": self.test_entities,
            "relationships": self.test_relationships
        }
        self.mock_llm.generate_content.return_value = mock_result
        
        # Call method under test
        result = self.engine._extract_query_structure(self.test_query)
        
        # Assertions
        self.assertEqual(len(result["entities"]), 2)
        self.assertEqual(result["entities"][0]["entity"], "Kevin Smith")
        self.assertEqual(result["relationships"], ["employment"])
        self.mock_llm.generate_content.assert_called_once()

    def test_query_knowledge_graph(self):
        """Test querying knowledge graph with structured info."""
        # Configure mock session to return raw Neo4j results
        self.mock_session.run().data.return_value = self.mock_neo4j_raw_results
        
        # Call method under test
        structured_info = {
            "entities": self.test_entities,
            "relationships": self.test_relationships
        }
        result = self.engine._query_knowledge_graph(structured_info)
        
        # Assertions - compare with expected processed results
        self.assertEqual(result, self.mock_graph_results)
        self.mock_session.run.assert_called_once()

    def test_vector_search(self):
        """Test vector similarity search."""
        # Configure mock embedding model and Neo4j session
        self.mock_session.run().data.return_value = self.mock_vector_results
        
        # Call method under test
        result = self.engine._vector_search(self.test_query)
        
        # Assertions
        self.assertEqual(result, self.mock_vector_results)
        self.mock_embedding_model.get_embedding.assert_called_once_with(self.test_query)
        self.mock_session.run.assert_called_once()

    def test_synthesize_response(self):
        """Test response synthesis with all retrieved information."""
        # Call method under test
        result = self.engine._synthesize_response(
            self.test_query,
            self.mock_graph_results,
            self.mock_vector_results
        )
        
        # Assertions
        self.assertEqual(result, "Generated response")
        self.mock_llm.generate_content.assert_called_once()

    def test_query_end_to_end(self):
        """Test the full query pipeline end-to-end."""
        # Configure all mocks for the pipeline
        mock_structure = {
            "entities": self.test_entities,
            "relationships": self.test_relationships
        }
        
        # Mock individual methods
        with patch.object(self.engine, '_extract_query_structure', return_value=mock_structure) as mock_extract:
            with patch.object(self.engine, '_query_knowledge_graph', return_value=self.mock_graph_results) as mock_graph:
                with patch.object(self.engine, '_vector_search', return_value=self.mock_vector_results) as mock_vector:
                    with patch.object(self.engine, '_synthesize_response', return_value="Final Answer") as mock_synth:
                        
                        # Call method under test
                        result = self.engine.query(self.test_query)
                        
                        # Assertions for pipeline
                        mock_extract.assert_called_once_with(self.test_query)
                        mock_graph.assert_called_once_with(mock_structure)
                        mock_vector.assert_called_once_with(self.test_query)
                        mock_synth.assert_called_once_with(self.test_query, self.mock_graph_results, self.mock_vector_results)
                        self.assertEqual(result.answer, "Final Answer")
                        self.assertEqual(result.graph_results, self.mock_graph_results)
                        self.assertEqual(result.vector_results, self.mock_vector_results)
    
    def test_empty_graph_results(self):
        """Test fallback to vector results when graph results are empty."""
        # Configure mock for pipeline with empty graph results
        mock_structure = {
            "entities": self.test_entities,
            "relationships": self.test_relationships
        }
        empty_graph_results = []
        
        # Mock individual methods
        with patch.object(self.engine, '_extract_query_structure', return_value=mock_structure) as mock_extract:
            with patch.object(self.engine, '_query_knowledge_graph', return_value=empty_graph_results) as mock_graph:
                with patch.object(self.engine, '_vector_search', return_value=self.mock_vector_results) as mock_vector:
                    with patch.object(self.engine, '_synthesize_response', return_value="Vector Only Answer") as mock_synth:
                        
                        # Call method under test
                        result = self.engine.query(self.test_query)
                        
                        # Assertions
                        mock_synth.assert_called_once_with(self.test_query, empty_graph_results, self.mock_vector_results)
                        self.assertEqual(result.answer, "Vector Only Answer")
                        self.assertEqual(result.graph_results, empty_graph_results)
                        self.assertEqual(result.vector_results, self.mock_vector_results)
    
    def test_error_handling(self):
        """Test error handling in the query pipeline."""
        # Mock extract_query_structure to raise an exception
        with patch.object(self.engine, '_extract_query_structure', side_effect=Exception("Test error")) as mock_extract:
            with patch.object(self.engine, '_vector_search', return_value=self.mock_vector_results) as mock_vector:
                with patch.object(self.engine, '_synthesize_response') as mock_synth:
                    
                    # Call method under test
                    result = self.engine.query(self.test_query)
                    
                    # Assertions - should fall back to vector search
                    mock_vector.assert_called_once()
                    # Should use only vector results in synthesis
                    mock_synth.assert_called_once_with(self.test_query, [], self.mock_vector_results)
                    # Verify response object contains error information
                    self.assertIsNotNone(result.error)
                    self.assertEqual(result.graph_results, [])
                    self.assertEqual(result.vector_results, self.mock_vector_results)


if __name__ == '__main__':
    unittest.main()
    # Can also run with: uv run pytest -m "unit" -xvs
