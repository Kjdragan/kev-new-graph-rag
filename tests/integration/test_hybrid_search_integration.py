"""
Integration tests for HybridSearchEngine

These tests interact with real Neo4j and Gemini APIs to validate
the hybrid search functionality in real-world conditions.

Note: These tests require valid API credentials in .env file.
"""
import os
import sys
import pytest
import time
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to sys.path to enable imports from project modules
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import project modules
from neo4j import GraphDatabase, Driver
from google import genai


# Import the module under test
from utils.hybrid_search_engine import HybridSearchEngine
from utils.embedding import CustomGeminiEmbedding
from utils.config import get_config

# Skip integration tests if environment is not configured
pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(project_root, ".env")),
    reason="Integration tests require .env file with valid credentials"
)


@pytest.fixture(scope="module")
def neo4j_driver():
    """Create a real Neo4j driver instance for testing."""
    # Load environment variables
    load_dotenv()

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    # Skip if any required env vars are missing
    if not all([uri, user, password]):
        pytest.skip("Neo4j credentials not configured in .env file")

    # Create driver
    driver = GraphDatabase.driver(uri, auth=(user, password))

    # Verify connection
    try:
        with driver.session() as session:
            result = session.run("RETURN 1 as test").single()
            if result["test"] != 1:
                pytest.skip("Failed to connect to Neo4j")
    except Exception as e:
        pytest.skip(f"Error connecting to Neo4j: {e}")

    yield driver

    # Cleanup
    driver.close()


@pytest.fixture(scope="module")
def gemini_models():
    """Create real Gemini model instances for testing."""
    # Load environment variables
    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")

    # Skip if API key is missing
    if not api_key:
        pytest.skip("Google API key not configured in .env file")

    # Configure Gemini
    genai.configure(api_key=api_key)

    # Get configuration
    config = get_config()

    # Create models
    llm = GenerativeModel(
        model_name=config.get_gemini_model_id("pro"),
        generation_config={
            "temperature": 0.2,
            "top_p": 0.9,
            "top_k": 30,
            "max_output_tokens": 2048,
        }
    )

    embedding_model = CustomGeminiEmbedding(
        model_name=config.get_gemini_embeddings_model(),
        task_type="retrieval_document",
        api_key=api_key
    )

    # Verify models
    try:
        # Test embedding model
        _ = embedding_model.get_embedding("Test embedding")

        # Test LLM
        response = llm.generate_content("Say hello")
        if not hasattr(response, "text") and not (hasattr(response, "candidates") and response.candidates):
            pytest.skip("Failed to get response from Gemini model")
    except Exception as e:
        pytest.skip(f"Error testing Gemini models: {e}")

    return {"llm": llm, "embedding_model": embedding_model}


@pytest.fixture
def hybrid_search_engine(neo4j_driver, gemini_models):
    """Create a real HybridSearchEngine instance for testing."""
    config = get_config()

    engine_config = {
        "thinking_budget": config.get_gemini_thinking_budget("pro"),
        "vector_top_k": config.get("hybrid_search.vector_top_k", 3),
        "similarity_threshold": config.get("hybrid_search.similarity_threshold", 0.6),
    }

    engine = HybridSearchEngine(
        neo4j_driver=neo4j_driver,
        embedding_model=gemini_models["embedding_model"],
        llm=gemini_models["llm"],
        config=engine_config
    )

    return engine


class TestHybridSearchIntegration:
    """Integration tests for HybridSearchEngine with real services."""

    def test_extract_query_structure(self, hybrid_search_engine):
        """Test entity and relationship extraction with real Gemini."""
        query = "Who is Kevin Smith and where does he work?"

        # Call the method
        result = hybrid_search_engine._extract_query_structure(query)

        # Basic validation
        assert "entities" in result
        assert isinstance(result["entities"], list)

        # Check if Kevin Smith was extracted as an entity
        entity_names = [e.get("entity", "").lower() for e in result["entities"]]
        assert any("kevin" in name for name in entity_names)

    def test_vector_search(self, hybrid_search_engine):
        """Test vector search with real Neo4j and embeddings."""
        query = "knowledge graph"

        # Call the method
        result = hybrid_search_engine._vector_search(query)

        # For integration tests, we can't assert exact responses,
        # just validate the structure and basic behavior
        assert isinstance(result, list)

        # If we got results, check their structure
        for item in result:
            assert "score" in item
            assert isinstance(item["score"], float)
            assert 0 <= item["score"] <= 1

    def test_full_query_pipeline(self, hybrid_search_engine):
        """Test the complete query pipeline with real services."""
        query = "What is hybrid search?"

        # Call the full query method
        start_time = time.time()
        response = hybrid_search_engine.query(query)
        elapsed_time = time.time() - start_time

        # Log timing information (useful for performance testing)
        print(f"\nQuery time: {elapsed_time:.2f} seconds")

        # Validate response structure
        assert hasattr(response, "answer")
        assert hasattr(response, "query")
        assert hasattr(response, "sources")

        # Check that the response makes sense
        assert len(response.answer) > 0
        assert query in response.query
