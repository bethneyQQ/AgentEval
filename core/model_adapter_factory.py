"""
Model Adapter Factory for managing different LLM providers.

This module provides a factory pattern for creating and managing model adapters,
with support for configuration-driven model registration.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from .model_adapter_base import ModelAdapter
from .model_litellm_adapter import LiteLLMAdapter

logger = logging.getLogger(__name__)


class ModelAdapterFactory:
    """Factory for creating model adapters."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the factory.

        Args:
            config_path: Path to models configuration YAML file.
                        If None, looks for config/models.yaml
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                      'config', 'models.yaml')

        self.config_path = config_path
        self.models_config = self._load_config()
        self._adapter_cache: Dict[str, ModelAdapter] = {}

    def _load_config(self) -> Dict[str, Any]:
        """Load models configuration from YAML file."""
        if not os.path.exists(self.config_path):
            logger.warning(f"Model config file not found: {self.config_path}")
            return {'models': {}}

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

            config = self._expand_env_vars(config)
            return config

        except Exception as e:
            logger.error(f"Failed to load model config: {str(e)}")
            return {'models': {}}

    def _expand_env_vars(self, config: Dict) -> Dict:
        """Expand environment variables in configuration."""
        if 'models' not in config:
            return config

        for model_name, model_config in config['models'].items():
            if 'api_key' in model_config and isinstance(model_config['api_key'], str):
                if model_config['api_key'].startswith('${') and model_config['api_key'].endswith('}'):
                    env_var = model_config['api_key'][2:-1]
                    model_config['api_key'] = os.getenv(env_var)

        return config

    def get_adapter(self, model_name: str) -> ModelAdapter:
        """
        Get model adapter instance (singleton pattern).

        Args:
            model_name: Name of the model as defined in config

        Returns:
            ModelAdapter instance

        Raises:
            ValueError: If model not found in configuration
        """
        if model_name in self._adapter_cache:
            return self._adapter_cache[model_name]

        if model_name not in self.models_config.get('models', {}):
            raise ValueError(f"Model {model_name} not found in configuration")

        model_config = self.models_config['models'][model_name]
        adapter_type = model_config.get('adapter_type', 'litellm')

        if adapter_type == 'litellm':
            adapter = LiteLLMAdapter(model_config)
        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")

        self._adapter_cache[model_name] = adapter
        logger.info(f"Created adapter for model: {model_name}")
        return adapter

    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """List all available models."""
        return self.models_config.get('models', {})

    def reload_config(self):
        """Reload configuration from file."""
        self.models_config = self._load_config()
        self._adapter_cache.clear()
        logger.info("Model configuration reloaded")
