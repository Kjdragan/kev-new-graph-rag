# utils/config_loader.py
# Centralized configuration loader for the application.

from loguru import logger
from typing import Optional
import os
import dotenv
from dotenv import find_dotenv

# The IngestionOrchestratorConfig seems to be the global config for data processing pipelines.
# We will use it as the main config object.
from .config import config as global_config
from .config_models import (
    GDriveReaderConfig,
    LlamaParseConfig,
    Neo4jConfig,
    ChromaDBConfig,
    EmbeddingConfig,
    IngestionOrchestratorConfig
)

def get_config(env_file: Optional[str] = None) -> IngestionOrchestratorConfig:
    """
    Load configuration from both the .env file (for secrets and environment-specific settings)
    and the config.yaml file (for model IDs and other application parameters).
    """
    # Load environment variables from .env file. Pydantic's BaseSettings will use these.
    dotenv.load_dotenv(env_file or find_dotenv() or '.env')
    
    # Instantiate config models, which will automatically load from environment variables
    gdrive_config = GDriveReaderConfig()
    llamaparse_config = LlamaParseConfig()
    neo4j_config = Neo4jConfig()
    chroma_config = ChromaDBConfig()
    
    # For EmbeddingConfig, we merge values from both sources:
    # 1. Get model parameters from config.yaml via the global_config singleton.
    embedding_model_name = global_config.get_gemini_embeddings_model()
    embedding_dimensions = global_config.get_gemini_embeddings_dimensionality()
    
    # 2. Instantiate EmbeddingConfig. It will load the GOOGLE_API_KEY from the .env file,
    #    and we explicitly provide the model name and dimensions from config.yaml.
    embedding_config = EmbeddingConfig(
        embedding_model_name=embedding_model_name,
        dimensions=embedding_dimensions,
        # The google_api_key is automatically loaded from the environment by Pydantic
    )
    
    # 3. Load the Gemini Suite config from the YAML file.
    gemini_suite_config = global_config.get_gemini_suite_config()

    # Assemble the final orchestrator configuration
    orchestrator_config = IngestionOrchestratorConfig(
        gdrive=gdrive_config,
        llamaparse=llamaparse_config,
        neo4j=neo4j_config,
        chromadb=chroma_config,
        embedding=embedding_config,
        gemini_suite=gemini_suite_config
    )
    
    return orchestrator_config
