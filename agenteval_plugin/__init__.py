"""
AgentEval Plugin System

A low-overhead plugin system for collecting agent execution traces.
"""

__version__ = "1.0.0"

import asyncio
from typing import Optional, Dict, Any

from .config import Config, init_config, get_config
from .core import plugin_manager, PluginManager, BasePlugin
from .plugins import EvaluationPlugin
from .trace import init_trace_collector, get_trace_collector
from .decorators import instrument_agent, instrument_agent_stream, instrument_node
from .utils import setup_logging, get_logger

logger = get_logger(__name__)


def init_plugin_system(
    config_path: Optional[str] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    auto_start: bool = True
) -> PluginManager:
    """
    Initialize the AgentEval plugin system

    Args:
        config_path: Path to YAML configuration file
        config_dict: Configuration dictionary (overrides file)
        auto_start: Automatically start trace collector

    Returns:
        PluginManager instance

    Example:
        >>> from agenteval_plugin import init_plugin_system
        >>> manager = init_plugin_system(config_path="config/agenteval.yaml")
    """
    # Load configuration
    if config_dict:
        config = init_config(config_dict=config_dict)
    elif config_path:
        config = init_config(config_path=config_path)
    else:
        config = init_config()

    # Setup logging
    log_level = config.get('global.log_level', 'INFO')
    log_file = config.get('global.log_file')
    setup_logging(level=log_level, log_file=log_file)

    logger.info(f"Initializing AgentEval Plugin System v{__version__}")

    # Check if enabled
    if not config.get('global.enabled', True):
        logger.info("AgentEval plugin system is disabled")
        return plugin_manager

    # Initialize trace collector
    trace_config = config.get_section('trace_collector')
    trace_config['privacy'] = config.get_section('privacy')
    trace_config['performance'] = config.get_section('performance')

    collector = init_trace_collector(trace_config)

    if auto_start:
        # Start collector in background
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(collector.start())
            else:
                loop.run_until_complete(collector.start())
        except RuntimeError:
            # No event loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(collector.start())

    # Register evaluation plugin
    eval_plugin = EvaluationPlugin()
    plugin_manager.register_plugin(eval_plugin)

    logger.info("AgentEval Plugin System initialized successfully")

    return plugin_manager


def shutdown_plugin_system():
    """
    Shutdown the plugin system and cleanup resources

    Example:
        >>> from agenteval_plugin import shutdown_plugin_system
        >>> shutdown_plugin_system()
    """
    logger.info("Shutting down AgentEval Plugin System")

    try:
        collector = get_trace_collector()
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(collector.stop())
        else:
            loop.run_until_complete(collector.stop())
    except Exception as e:
        logger.error(f"Error stopping trace collector: {e}")

    logger.info("AgentEval Plugin System shutdown complete")


# Convenience exports
__all__ = [
    '__version__',
    'init_plugin_system',
    'shutdown_plugin_system',
    'instrument_agent',
    'instrument_agent_stream',
    'instrument_node',
    'plugin_manager',
    'PluginManager',
    'BasePlugin',
    'EvaluationPlugin',
    'Config',
    'get_config',
]
