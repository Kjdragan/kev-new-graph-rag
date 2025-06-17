"""
Configuration utility for Kevin's "kev-new-graph-rag" project.
Loads and provides access to configuration values from config.yaml
"""
import os
import yaml
import logging
from typing import Dict, Any, Optional
from utils.config_models import GeminiModelInstanceConfig, GeminiSuiteConfig # Added import

# Set up logging
logger = logging.getLogger(__name__)

# Default config path relative to project root
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")

class Config:
    """Configuration manager for the Graph-RAG project"""

    _instance = None
    _config_data = None

    def __new__(cls, config_path: Optional[str] = None):
        """Singleton pattern to ensure only one config instance exists"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config(config_path or CONFIG_PATH)
        return cls._instance

    def _load_config(self, config_path: str):
        """Load configuration from the specified YAML file"""
        try:
            with open(config_path, 'r') as f:
                self._config_data = yaml.safe_load(f)
                logger.info(f"Configuration loaded from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            self._config_data = {}

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation path

        Args:
            path: Dot notation path to the config value (e.g., "gemini.models.pro.model_id")
            default: Default value to return if path not found

        Returns:
            The configuration value or default if not found
        """
        parts = path.split('.')
        current = self._config_data

        for part in parts:
            if current is None or not isinstance(current, dict) or part not in current:
                return default
            current = current[part]

        return current

    def get_gemini_model_id(self, model_type: str = "flash") -> str:
        """
        Get the Gemini model ID for the specified model type

        Args:
            model_type: Either "pro" or "flash"

        Returns:
            The model ID string
        """
        if model_type.lower() not in ["pro", "flash"]:
            logger.warning(f"Unknown model type: {model_type}, defaulting to flash")
            model_type = "flash"

        return self.get(f"gemini.models.{model_type.lower()}.model_id")

    def get_gemini_thinking_budget(self, model_type: str = "flash") -> int:
        """
        Get the thinking budget for the specified model type

        Args:
            model_type: Either "pro" or "flash"

        Returns:
            The thinking budget as an integer
        """
        if model_type.lower() not in ["pro", "flash"]:
            logger.warning(f"Unknown model type: {model_type}, defaulting to flash")
            model_type = "flash"

        return self.get(f"gemini.models.{model_type.lower()}.thinking_budget", 0)

    def get_gemini_embeddings_model(self) -> str:
        """Get the Gemini embeddings model ID"""
        return self.get("gemini.embeddings.model_id", "embedding-001")
        
    def get_gemini_embeddings_dimensionality(self) -> int:
        """Get the Gemini embeddings output dimensionality"""
        return self.get("gemini.embeddings.output_dimensionality", 1536)

    def get_gemini_suite_config(self) -> GeminiSuiteConfig:
        """Get the Gemini LLM suite configuration."""
        pro_model_data = self.get("gemini.models.pro", {})
        flash_model_data = self.get("gemini.models.flash", {})

        if not pro_model_data.get("model_id"):
            logger.warning("Pro model configuration or model_id is missing in config.yaml. Defaults or Pydantic validation will apply.")
        if not flash_model_data.get("model_id"):
            logger.warning("Flash model configuration or model_id is missing in config.yaml. Defaults or Pydantic validation will apply.")

        # Pydantic will raise a ValidationError if 'model_id' is missing, as it's required.
        # We pass the dict directly; Pydantic handles field mapping.
        pro_model_config = GeminiModelInstanceConfig(**pro_model_data) 
        flash_model_config = GeminiModelInstanceConfig(**flash_model_data)

        return GeminiSuiteConfig(
            pro_model=pro_model_config,
            flash_model=flash_model_config
        )

# Create a default config instance
config = Config()

# For direct imports
def get_config() -> Config:
    """Get the configuration instance"""
    return config
