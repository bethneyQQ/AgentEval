"""
ADEWorker Plugin Integration Module

This module provides a ready-to-use integration for ADEWorker.
Simply copy this file to your ADEWorker project and use the decorators.

Usage:
    1. Copy this file to: backend/worker/agent/plugins/agenteval_plugin.py
    2. Initialize in your startup: init_agenteval()
    3. Add decorators to your agent methods
"""

import os
import sys
import time
import functools
from typing import Callable, Optional, Any
import logging

# Add AgentEval to path
AGENTEVAL_PATH = os.environ.get('AGENTEVAL_PATH', '/home/shared/zqq/AgentEval')
if AGENTEVAL_PATH not in sys.path:
    sys.path.insert(0, AGENTEVAL_PATH)

logger = logging.getLogger(__name__)


class AgentEvalPluginWrapper:
    """Wrapper class to handle plugin initialization and operations"""

    def __init__(self):
        self.enabled = False
        self.plugin_manager = None
        self.initialized = False

    def initialize(self, config_path: Optional[str] = None):
        """Initialize the AgentEval plugin system"""
        try:
            from agenteval_plugin import init_plugin_system, plugin_manager
            from agenteval_plugin.core import AgentContext, NodeContext

            # Store for later use
            self.AgentContext = AgentContext
            self.NodeContext = NodeContext

            # Initialize plugin system
            if config_path:
                self.plugin_manager = init_plugin_system(config_path=config_path)
            else:
                # Use default config or environment variables
                self.plugin_manager = init_plugin_system()

            self.enabled = True
            self.initialized = True
            logger.info("AgentEval plugin initialized successfully")

        except Exception as e:
            logger.warning(f"Failed to initialize AgentEval plugin: {e}")
            logger.warning("Continuing without trace collection")
            self.enabled = False

    def shutdown(self):
        """Shutdown the plugin system"""
        if self.enabled and self.initialized:
            try:
                from agenteval_plugin import shutdown_plugin_system
                shutdown_plugin_system()
                logger.info("AgentEval plugin shutdown complete")
            except Exception as e:
                logger.error(f"Error during plugin shutdown: {e}")


# Global instance
_plugin_wrapper = AgentEvalPluginWrapper()


def init_agenteval(config_path: Optional[str] = None):
    """
    Initialize AgentEval plugin system

    Args:
        config_path: Path to configuration YAML file

    Example:
        # In your startup code
        from worker.agent.plugins.agenteval_plugin import init_agenteval
        init_agenteval(config_path="/path/to/config/agenteval_plugin.yaml")
    """
    _plugin_wrapper.initialize(config_path)


def shutdown_agenteval():
    """
    Shutdown AgentEval plugin system

    Example:
        # In your shutdown code
        from worker.agent.plugins.agenteval_plugin import shutdown_agenteval
        shutdown_agenteval()
    """
    _plugin_wrapper.shutdown()


def instrument_agent(agent_type: str, agent_version: str = "1.0.0"):
    """
    Decorator for instrumenting agent methods (arun/astream_run)

    Args:
        agent_type: Type of agent (e.g., "DevAgent", "PMAgent")
        agent_version: Version string

    Example:
        @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
        async def arun(self, user_input: UserInput) -> DevState:
            # Your code here
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, user_input, *args, **kwargs):
            # If plugin not enabled, just run original function
            if not _plugin_wrapper.enabled:
                return await func(self, user_input, *args, **kwargs)

            try:
                # Create agent context
                context = _plugin_wrapper.AgentContext(
                    agent_id=f"{agent_type}_{user_input.task_id}",
                    agent_type=agent_type,
                    agent_version=agent_version,
                    session_id=getattr(user_input, 'session_id', ''),
                    user_id=getattr(user_input, 'user_id', ''),
                    task_id=user_input.task_id,
                    workspace_path=getattr(user_input, 'repo_ws_path', ''),
                    start_time=time.time(),
                    metadata={
                        'task_desc': getattr(user_input, 'task_desc', ''),
                    }
                )

                # Store context in user_input for node access
                user_input._agent_context = context

                # Trigger on_agent_start
                await _plugin_wrapper.plugin_manager.trigger_agent_start(context)

                result = None
                error = None
                try:
                    result = await func(self, user_input, *args, **kwargs)
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    await _plugin_wrapper.plugin_manager.trigger_agent_end(context, result, error)

            except Exception as e:
                logger.error(f"Error in plugin instrumentation: {e}", exc_info=True)
                # If plugin fails, still run the original function
                return await func(self, user_input, *args, **kwargs)

        return wrapper
    return decorator


def instrument_node(node_name: str):
    """
    Decorator for instrumenting LangGraph node methods

    Args:
        node_name: Name of the node (e.g., "gen_code", "understand_repo")

    Example:
        @instrument_node(node_name="gen_code")
        def _node_gen_code(self, state: DevState) -> DevState:
            # Your code here
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(self, state, *args, **kwargs):
            # If plugin not enabled, just run original function
            if not _plugin_wrapper.enabled:
                return func(self, state, *args, **kwargs)

            try:
                # Try to get agent context from state
                agent_context = None
                if hasattr(state, 'input') and hasattr(state.input, '_agent_context'):
                    agent_context = state.input._agent_context

                if not agent_context:
                    # No context, run without instrumentation
                    return func(self, state, *args, **kwargs)

                # Create node context
                node_context = _plugin_wrapper.NodeContext(
                    node_name=node_name,
                    start_time=time.time(),
                    input_state=state.model_dump() if hasattr(state, 'model_dump') else {}
                )

                # Trigger on_node_start (create task to not block)
                import asyncio
                try:
                    asyncio.create_task(
                        _plugin_wrapper.plugin_manager.trigger_node_start(agent_context, node_context)
                    )
                except RuntimeError:
                    # No event loop running, skip
                    pass

                output_state = None
                error = None
                try:
                    output_state = func(self, state, *args, **kwargs)
                    return output_state
                except Exception as e:
                    error = e
                    raise
                finally:
                    # Trigger on_node_end
                    try:
                        output_dict = output_state.model_dump() if output_state and hasattr(output_state, 'model_dump') else {}
                        asyncio.create_task(
                            _plugin_wrapper.plugin_manager.trigger_node_end(
                                agent_context, node_context, output_dict, error
                            )
                        )
                    except RuntimeError:
                        pass

            except Exception as e:
                logger.debug(f"Error in node instrumentation: {e}")
                # If plugin fails, still run the original function
                return func(self, state, *args, **kwargs)

        return wrapper
    return decorator


# Convenience exports
__all__ = [
    'init_agenteval',
    'shutdown_agenteval',
    'instrument_agent',
    'instrument_node',
]
