"""
Test ChromaDB connection and basic functionality.
Run with: uv run scripts/test_chroma_connection.py
"""

import os
import sys
from pathlib import Path
import uuid

import chromadb
import dotenv
from loguru import logger

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.config_models import ChromaDBConfig
from utils.embedding import CustomGeminiEmbedding
from utils.chroma_ingester import ChromaIngester
from utils.config import Config

def main():
    """Test ChromaDB connection and functionality."""
    # Load environment variables
    dotenv.load_dotenv()

    # Initialize config
    config = Config()

    # Get embedding configuration
    embedding_model_name = config.get("gemini.embeddings.model_id")
    embedding_dimensions = config.get("gemini.embeddings.output_dimensionality")

    # Create ChromaDB config
    chroma_config = ChromaDBConfig(
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", "8000")),
        collection_name=f"test_collection_{str(uuid.uuid4())[:8]}",  # Use a test collection
        auth_enabled=os.getenv("CHROMA_AUTH_ENABLED", "false").lower() == "true",
        username=os.getenv("CHROMA_USERNAME", "admin"),
        password=os.getenv("CHROMA_PASSWORD", "admin123")
    )

    # Initialize embedding model
    embedding_model = CustomGeminiEmbedding(
        model_name=embedding_model_name,
        output_dimensionality=embedding_dimensions,
        google_api_key=os.getenv("GOOGLE_API_KEY", "")
    )

    logger.info(f"Testing ChromaDB connection to {chroma_config.host}:{chroma_config.port}...")

    try:
        # Initialize ChromaDB ingester
        ingester = ChromaIngester(chroma_config, embedding_model)

        # Generate a test document and embedding
        test_doc = {
            "id": f"test_doc_{uuid.uuid4()}",
            "text": "This is a test document to verify ChromaDB connection and functionality.",
            "metadata": {
                "source": "test_script",
                "test_id": str(uuid.uuid4())
            }
        }

        logger.info("Ingesting test document...")
        result = ingester.ingest_documents([test_doc])

        if result:
            logger.info("✅ Successfully ingested test document")

            # Test search functionality
            logger.info("Testing search functionality...")
            search_results = ingester.search(
                query="test document",
                n_results=1
            )

            if search_results and len(search_results["documents"][0]) > 0:
                logger.info("✅ Search functionality working correctly")
                logger.info(f"Found document: {search_results['documents'][0][0][:50]}...")
                logger.info(f"With distance: {search_results['distances'][0][0]}")
            else:
                logger.error("❌ Search functionality failed")

            # Clean up the test collection
            logger.info("Cleaning up test collection...")
            ingester.client.delete_collection(chroma_config.collection_name)
            logger.info("✅ Test collection deleted")

            logger.info("All tests passed! ChromaDB is configured correctly.")
        else:
            logger.error("❌ Failed to ingest test document")

    except Exception as e:
        logger.error(f"❌ ChromaDB test failed: {str(e)}")
        logger.exception("Exception details:")
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
