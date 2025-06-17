import chromadb
import sys
from pathlib import Path
from loguru import logger

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config_loader import get_config

def clear_chroma_collection():
    """Connects to ChromaDB, deletes, and recreates the specified collection."""
    try:
        # Load configuration from .env and config.yaml
        config = get_config()
        chroma_config = config.chromadb

        logger.info(f"Connecting to ChromaDB at {chroma_config.host}:{chroma_config.port}...")
        client = chromadb.HttpClient(host=chroma_config.host, port=chroma_config.port)

        collection_name = chroma_config.collection_name
        logger.info(f"Target collection: '{collection_name}'")

        # Check if the collection exists and delete it
        collections = client.list_collections()
        if any(c.name == collection_name for c in collections):
            logger.info(f"Collection '{collection_name}' exists. Attempting to delete...")
            try:
                client.delete_collection(name=collection_name)
                logger.success(f"Successfully deleted collection '{collection_name}'.")
            except Exception as e:
                logger.error(f"Failed to delete existing collection '{collection_name}': {e}", exc_info=True)
                raise
        else:
            logger.info(f"Collection '{collection_name}' does not exist. No deletion needed.")

        # Recreate the collection
        logger.info(f"Recreating collection '{collection_name}'...")
        client.get_or_create_collection(
            name=collection_name,
        )
        logger.success(f"Successfully created or ensured collection '{collection_name}' exists.")
        logger.info("ChromaDB collection is now clean and ready.")

    except Exception as e:
        logger.error(f"An error occurred while clearing the ChromaDB collection: {str(e)}", exc_info=True)
        raise  # Re-raise the exception to ensure non-zero exit code if called as a module function

if __name__ == "__main__":
    try:
        clear_chroma_collection()
    except Exception:
        sys.exit(1) # Ensure script exits with error code if an exception was raised
