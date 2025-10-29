"""
Configuration Management

Loads and manages plugin configuration from YAML files and environment variables.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


DEFAULT_CONFIG = {
    'global': {
        'enabled': True,
        'log_level': 'INFO',
    },
    'trace_collector': {
        'enabled': True,
        'endpoint': 'http://localhost:8000',
        'api_key': '',
        'batch': {
            'max_size': 100,
            'max_wait_seconds': 1.0,
            'max_queue_size': 10000,
        },
        'retry': {
            'max_attempts': 3,
            'backoff_factor': 2.0,
            'max_backoff_seconds': 60,
        },
        'sampling': {
            'rate': 1.0,
            'rules': [],
        },
        'local_cache': {
            'enabled': True,
            'cache_dir': '/tmp/agenteval_cache',
            'max_size_mb': 1000,
            'ttl_hours': 24,
        },
    },
    'privacy': {
        'enabled': True,
        'sensitive_fields': [
            'password', 'token', 'api_key', 'secret', 'private_key',
            'access_token', 'refresh_token', 'session_token'
        ],
        'redact_patterns': [
            {
                'pattern': r'sk-[a-zA-Z0-9]{32,}',
                'replacement': 'sk-***REDACTED***'
            },
            {
                'pattern': r'ghp_[a-zA-Z0-9]{36}',
                'replacement': 'ghp_***REDACTED***'
            },
        ],
    },
    'performance': {
        'async_mode': True,
        'max_concurrent_uploads': 5,
        'use_compression': True,
    },
}


class Config:
    """Configuration manager"""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self._config = DEFAULT_CONFIG.copy()
        if config_dict:
            self._deep_update(self._config, config_dict)

    @classmethod
    def from_file(cls, config_path: str) -> 'Config':
        """Load configuration from YAML file"""
        config_path = Path(config_path)
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return cls()

        try:
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f)

            # Substitute environment variables
            config_dict = cls._substitute_env_vars(config_dict)

            logger.info(f"Loaded configuration from {config_path}")
            return cls(config_dict)
        except Exception as e:
            logger.error(f"Failed to load config file: {e}", exc_info=True)
            return cls()

    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        config_dict = DEFAULT_CONFIG.copy()

        # Override with environment variables
        if 'AGENTEVAL_ENABLED' in os.environ:
            config_dict['global']['enabled'] = os.environ['AGENTEVAL_ENABLED'].lower() == 'true'

        if 'AGENTEVAL_ENDPOINT' in os.environ:
            config_dict['trace_collector']['endpoint'] = os.environ['AGENTEVAL_ENDPOINT']

        if 'AGENTEVAL_API_KEY' in os.environ:
            config_dict['trace_collector']['api_key'] = os.environ['AGENTEVAL_API_KEY']

        if 'AGENTEVAL_LOG_LEVEL' in os.environ:
            config_dict['global']['log_level'] = os.environ['AGENTEVAL_LOG_LEVEL']

        if 'AGENTEVAL_SAMPLING_RATE' in os.environ:
            try:
                config_dict['trace_collector']['sampling']['rate'] = float(os.environ['AGENTEVAL_SAMPLING_RATE'])
            except ValueError:
                logger.warning("Invalid AGENTEVAL_SAMPLING_RATE, using default")

        return cls(config_dict)

    @staticmethod
    def _substitute_env_vars(config: Any) -> Any:
        """Recursively substitute ${VAR_NAME} with environment variables"""
        if isinstance(config, dict):
            return {k: Config._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [Config._substitute_env_vars(v) for v in config]
        elif isinstance(config, str):
            # Replace ${VAR} or $VAR patterns
            import re
            pattern = r'\$\{([^}]+)\}|\$([A-Z_][A-Z0-9_]*)'

            def replace(match):
                var_name = match.group(1) or match.group(2)
                return os.environ.get(var_name, match.group(0))

            return re.sub(pattern, replace, config)
        else:
            return config

    @staticmethod
    def _deep_update(base: Dict, update: Dict) -> None:
        """Deep update base dict with update dict"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                Config._deep_update(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self._config.get(section, {})

    def to_dict(self) -> Dict[str, Any]:
        """Get entire configuration as dictionary"""
        return self._config.copy()


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance"""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def init_config(config_path: Optional[str] = None, config_dict: Optional[Dict] = None) -> Config:
    """Initialize global config"""
    global _config

    if config_path:
        _config = Config.from_file(config_path)
    elif config_dict:
        _config = Config(config_dict)
    else:
        _config = Config.from_env()

    return _config
