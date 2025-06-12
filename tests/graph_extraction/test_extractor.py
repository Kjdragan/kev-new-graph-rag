# tests/graph_extraction/test_extractor.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from pydantic import BaseModel # For defining mock node/edge types if needed

# Module to test
from src.graph_extraction.extractor import GraphExtractor
from src.ontology_templates.generic_ontology import BaseNode, BaseRelationship
from graphiti_core.llm_client import LLMConfig
from graphiti_core.nodes import EpisodeType, EpisodicNode # For mocking and assertions
from graphiti_core.graphiti import AddEpisodeResults # For mocking and assertions

# Mock config object
class MockConfig:
    def __init__(self):
        self.gemini_model_name_graph_extraction = "gemini-test-model"
        # Add other config attrs if GraphExtractor uses them in future

@pytest.fixture
def mock_config_data():
    return MockConfig()

@pytest.fixture
def mock_add_episode_results():
    # Create a mock AddEpisodeResults object that mimics graphiti's output
    mock_results = MagicMock(spec=AddEpisodeResults)
    mock_results.nodes = [MagicMock()] # Example: list of mocked nodes
    mock_results.edges = [MagicMock()] # Example: list of mocked edges
    mock_results.episode = MagicMock(spec=EpisodicNode)
    mock_results.episode.name = "mock_episode_name"
    # model_dump() is called on the result
    mock_results.model_dump.return_value = {
        "nodes": [{"id": "node1"}], 
        "edges": [{"id": "edge1"}], 
        "episode": {"name": "mock_episode_name"}
    }
    return mock_results

@pytest.mark.asyncio
class TestGraphExtractor:

    @patch('src.graph_extraction.extractor.get_config')
    @patch('src.graph_extraction.extractor.GeminiClient')
    @patch('src.graph_extraction.extractor.Graphiti')
    async def test_initialization(self, MockGraphiti, MockGeminiClient, mock_get_config, mock_config_data):
        mock_get_config.return_value = mock_config_data
        mock_gemini_instance = MockGeminiClient.return_value
        mock_graphiti_instance = MockGraphiti.return_value
        # Ensure graphiti_instance.close is an AsyncMock for await
        mock_graphiti_instance.close = AsyncMock()

        extractor = GraphExtractor(
            neo4j_uri="bolt://mockhost:7687",
            neo4j_user="mockuser",
            neo4j_pass="mockpass",
            gemini_api_key="mockapikey"
        )

        mock_get_config.assert_called_once()
        
        # Check GeminiClient instantiation
        args_gemini, kwargs_gemini = MockGeminiClient.call_args
        called_llm_config = kwargs_gemini.get('config')
        assert isinstance(called_llm_config, LLMConfig)
        assert called_llm_config.model == "gemini-test-model"
        assert called_llm_config.api_key == "mockapikey"

        # Check Graphiti instantiation
        MockGraphiti.assert_called_once_with(
            uri="bolt://mockhost:7687",
            user="mockuser",
            password="mockpass",
            llm_client=mock_gemini_instance
        )
        assert extractor.graphiti_llm == mock_gemini_instance
        assert extractor.graphiti_instance == mock_graphiti_instance

        # Test close method to ensure mocks are correctly set up for it
        await extractor.close()
        mock_graphiti_instance.close.assert_awaited_once()

    @patch('src.graph_extraction.extractor.get_config')
    @patch('src.graph_extraction.extractor.uuid.uuid4', return_value="mock-uuid-123") # Mock uuid
    @patch.object(GraphExtractor, '__init__', lambda self, *args, **kwargs: None) # Bypass __init__
    async def test_extract_successful(self, mock_uuid4, mock_get_config_ignored, mock_config_data, mock_add_episode_results):
        # Manually set up the extractor instance with mocks
        extractor = GraphExtractor.__new__(GraphExtractor)
        extractor.config = mock_config_data # Manually set config
        extractor.graphiti_instance = MagicMock() # Mock the Graphiti instance
        extractor.graphiti_instance.add_episode = AsyncMock(return_value=mock_add_episode_results)
        
        # Define dummy ontology for testing
        class TestNode(BaseNode): label: str = "TestNode"
        class TestRelationship(BaseRelationship): type: str = "TEST_RELATES_TO"
        
        ontology_nodes = [TestNode]
        ontology_edges = [TestRelationship]
        text_content = "This is a test document for extraction."

        expected_dump = mock_add_episode_results.model_dump.return_value
        actual_result = await extractor.extract(
            text_content=text_content,
            ontology_nodes=ontology_nodes,
            ontology_edges=ontology_edges,
            group_id="test_group_alpha",
            episode_name_prefix="test_doc"
        )

        expected_entity_types_map = {"TestNode": TestNode}
        expected_edge_types_map = {"TestRelationship": TestRelationship}

        extractor.graphiti_instance.add_episode.assert_awaited_once_with(
            name="test_doc_mock-uuid-123",
            content=text_content,
            source=EpisodeType.text, 
            source_description="Document processed for KG extraction via GraphExtractor",
            group_id="test_group_alpha",
            entity_types=expected_entity_types_map,
            edge_types=expected_edge_types_map
        )
        assert actual_result == expected_dump
        mock_add_episode_results.model_dump.assert_called_once()

    @patch('src.graph_extraction.extractor.get_config')
    @patch.object(GraphExtractor, '__init__', lambda self, *args, **kwargs: None) # Bypass __init__
    async def test_extract_handles_graphiti_error(self, mock_get_config_ignored, mock_config_data):
        extractor = GraphExtractor.__new__(GraphExtractor)
        extractor.config = mock_config_data
        
        extractor.graphiti_instance = MagicMock()
        # Configure add_episode to raise an error
        error_message = "Simulated Graphiti API error"
        extractor.graphiti_instance.add_episode = AsyncMock(side_effect=ValueError(error_message))

        class TestNode(BaseNode): label: str = "TestNodeErr"
        ontology_nodes = [TestNode]
        ontology_edges = [] # No edges for simplicity
        text_content = "Document that causes an error."

        with pytest.raises(ValueError, match=error_message):
            await extractor.extract(
                text_content=text_content,
                ontology_nodes=ontology_nodes,
                ontology_edges=ontology_edges
            )
        
        # Ensure add_episode was still called
        extractor.graphiti_instance.add_episode.assert_awaited_once()
