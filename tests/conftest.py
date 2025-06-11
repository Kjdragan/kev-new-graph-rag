"""
Test configuration fixtures and utilities for Graph-RAG tests.

This module provides shared fixtures and configuration mocking for all tests,
ensuring consistent test environment and proper isolation.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Dict, Any

# Add the parent directory to sys.path to enable imports from project modules
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import project utilities
from utils.config import Config


@pytest.fixture
def mock_config():
    """Mock configuration with test values."""
    mock_config_obj = MagicMock(spec=Config)
    
    # Setup common config getters
    mock_config_obj.get.side_effect = lambda path, default=None: {
        "gemini.models.pro.model_id": "gemini-2.5-pro-preview-06-05",
        "gemini.models.pro.thinking_budget": 1024,
        "gemini.embeddings.model_id": "embedding-001",
        "neo4j.retry.max_retries": 3,
        "neo4j.retry.delay_seconds": 1.0,
        "hybrid_search.vector_top_k": 3,
        "hybrid_search.similarity_threshold": 0.6,
    }.get(path, default)
    
    # Setup specific getters
    mock_config_obj.get_gemini_model_id.return_value = "gemini-2.5-pro-preview-06-05"
    mock_config_obj.get_gemini_thinking_budget.return_value = 1024
    mock_config_obj.get_gemini_embeddings_model.return_value = "embedding-001"
    
    return mock_config_obj


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    env_vars = {
        "NEO4J_URI": "neo4j://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "test_password",
        "GOOGLE_API_KEY": "test_api_key"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars
