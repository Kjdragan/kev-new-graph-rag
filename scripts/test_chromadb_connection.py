"""
Simple script to test ChromaDB connectivity and basic functionality.
"""

import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import dotenv
from loguru import logger

from utils.chroma_ingester import ChromaIngester
from utils.embedding import CustomGeminiEmbedding
from utils.config import Config
from utils.config_models import ChromaDBConfig

# Load environment variables
dotenv.load_dotenv()

def main():
    """Test ChromaDB connection and basic functionality."""
    logger.info("Testing ChromaDB connection...")
    
    # Load config
    config = Config()
    embedding_model_name = config.get("models.embeddings.model")
    embedding_dimensions = config.get("models.embeddings.dimensions")
    
    # Initialize embedding model
    embedding_model = CustomGeminiEmbedding(
        model_name=embedding_model_name,
        output_dimensionality=embedding_dimensions,
        google_api_key=os.getenv("GOOGLE_API_KEY", "")
    )
    
    # ChromaDB connection parameters
    host = os.getenv("CHROMA_HOST", "localhost")
    port = int(os.getenv("CHROMA_PORT", "8000"))
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "documents_test")
    auth_enabled = os.getenv("CHROMA_AUTH_ENABLED", "false").lower() == "true"
    username = os.getenv("CHROMA_USERNAME", "admin")
    password = os.getenv("CHROMA_PASSWORD", "admin123")
    
    logger.info(f"Connecting to ChromaDB at {host}:{port} with collection '{collection_name}'")
    
    # Create ChromaDBConfig object
    chroma_config = ChromaDBConfig(
        host=host,
        port=port,
        collection_name=collection_name,
        auth_enabled=auth_enabled,
        username=username,
        password=password
    )
    
    # Create ChromaIngester
    chroma_ingester = ChromaIngester(
        config=chroma_config,
        embedding_model=embedding_model
    )
    
    # Test connection by creating/getting collection
    try:
        collection = chroma_ingester.get_or_create_collection()
        logger.info(f"Successfully connected to ChromaDB and accessed collection '{collection_name}'")
        count = chroma_ingester.count_documents()
        logger.info(f"Collection contains {count} documents")
        
        # Add a test document if collection is empty
        if count == 0:
            logger.info("Adding test document...")
            documents = ["This is a test document to verify ChromaDB functionality"]
            metadata = [{"source": "test_script", "test_id": "connection_test"}]
            ids = ["test_doc_1"]
            
            chroma_ingester.add_documents(documents, metadatas=metadata, ids=ids)
            logger.info("Test document added successfully")
            
            # Verify document was added
            count = chroma_ingester.count_documents()
            logger.info(f"Collection now contains {count} documents")
        
        # Test search functionality
        logger.info("Testing search functionality...")
        results = chroma_ingester.search("test document", n_results=1)
        
        if results:
            logger.info(f"Search successful! Found {len(results['documents'][0])} result(s)")
            logger.info(f"Document: {results['documents'][0]}")
            logger.info(f"Metadata: {results['metadatas'][0]}")
            logger.info(f"Distance: {results['distances'][0]}")
        else:
            logger.error("Search returned no results")
        
        logger.info("ChromaDB connection test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nChromaDB connection test: PASSED ✅")
        sys.exit(0)
    else:
        print("\nChromaDB connection test: FAILED ❌")
        sys.exit(1)
