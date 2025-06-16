# utils/config_loader.py
# Centralized configuration loader for the application.

from loguru import logger
from typing import Optional

# The IngestionOrchestratorConfig seems to be the global config for data processing pipelines.
# We will use it as the main config object.
from .config_models import IngestionOrchestratorConfig

_config_instance: Optional[IngestionOrchestratorConfig] = None

def get_config() -> IngestionOrchestratorConfig:
    """
    Loads the global ingestion configuration from environment variables and returns it.
    Implements a singleton pattern to ensure the config is loaded only once.
    """
    global _config_instance
    if _config_instance is None:
        logger.info("Loading IngestionOrchestratorConfig for the first time...")
        try:
            # Pydantic V2 will automatically read from environment variables
            # for the fields in the model and its sub-models if they are set.
            # e.g., LLAMAPARSE_API_KEY for the api_key field in LlamaParseConfig.
            _config_instance = IngestionOrchestratorConfig()
            logger.success("IngestionOrchestratorConfig loaded successfully.")
        except Exception as e:
            logger.error("Failed to load IngestionOrchestratorConfig. Ensure all required environment variables are set.", exc_info=True)
            raise
    return _config_instance
