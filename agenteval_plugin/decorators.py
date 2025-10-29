"""
Instrumentation Decorators

Provides decorators for instrumenting agent methods with minimal code changes.
"""

import time
import functools
from typing import Callable, Optional, Any
import logging

from .core.plugin_manager import plugin_manager
from .core.plugin_base import AgentContext, NodeContext, LLMContext

logger = logging.getLogger(__name__)


def instrument_agent(
    agent_type: str,
    agent_version: str = "1.0.0"
):
    """Decorator for instrumenting agent arun/astream_run methods

    Usage:
        @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
        async def arun(self, user_input):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, user_input, *args, **kwargs):
            # Extract context from user_input
            context = AgentContext(
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
            await plugin_manager.trigger_agent_start(context)

            result = None
            error = None
            try:
                # Execute original method
                result = await func(self, user_input, *args, **kwargs)
                return result
            except Exception as e:
                error = e
                logger.error(f"Agent execution failed: {e}", exc_info=True)
                raise
            finally:
                # Trigger on_agent_end
                await plugin_manager.trigger_agent_end(context, result, error)

        return wrapper
    return decorator


def instrument_agent_stream(
    agent_type: str,
    agent_version: str = "1.0.0"
):
    """Decorator for instrumenting streaming agent methods

    Usage:
        @instrument_agent_stream(agent_type="DevAgent")
        async def astream_run(self, user_input):
            async for state in ...:
                yield state
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, user_input, *args, **kwargs):
            # Extract context
            context = AgentContext(
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

            user_input._agent_context = context

            await plugin_manager.trigger_agent_start(context)

            error = None
            try:
                async for item in func(self, user_input, *args, **kwargs):
                    yield item
            except Exception as e:
                error = e
                raise
            finally:
                await plugin_manager.trigger_agent_end(context, None, error)

        return wrapper
    return decorator


def instrument_node(node_name: str):
    """Decorator for instrumenting LangGraph node methods

    Usage:
        @instrument_node(node_name="gen_code")
        def _node_gen_code(self, state):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(self, state, *args, **kwargs):
            # Try to get agent context from state or user_input
            agent_context = None
            if hasattr(state, 'input') and hasattr(state.input, '_agent_context'):
                agent_context = state.input._agent_context

            if not agent_context:
                # No context available, just execute without instrumentation
                return func(self, state, *args, **kwargs)

            # Create node context
            node_context = NodeContext(
                node_name=node_name,
                start_time=time.time(),
                input_state=state.model_dump() if hasattr(state, 'model_dump') else {}
            )

            # Trigger on_node_start (sync wrapper for async call)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Already in async context, create task
                    asyncio.create_task(plugin_manager.trigger_node_start(agent_context, node_context))
                else:
                    # Not in async context, run
                    loop.run_until_complete(plugin_manager.trigger_node_start(agent_context, node_context))
            except Exception as e:
                logger.debug(f"Could not trigger node start: {e}")

            output_state = None
            error = None
            try:
                # Execute original method
                output_state = func(self, state, *args, **kwargs)
                return output_state
            except Exception as e:
                error = e
                raise
            finally:
                # Trigger on_node_end
                try:
                    output_dict = output_state.model_dump() if output_state and hasattr(output_state, 'model_dump') else {}
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(plugin_manager.trigger_node_end(
                            agent_context, node_context, output_dict, error
                        ))
                    else:
                        loop.run_until_complete(plugin_manager.trigger_node_end(
                            agent_context, node_context, output_dict, error
                        ))
                except Exception as e:
                    logger.debug(f"Could not trigger node end: {e}")

        return wrapper
    return decorator


def instrument_llm_call(model_name: str = "unknown"):
    """Decorator for instrumenting LLM calls

    Usage:
        @instrument_llm_call(model_name="gpt-4")
        async def call_llm(self, prompt, **kwargs):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Extract prompt from args or kwargs
            prompt = kwargs.get('prompt', args[0] if args else '')

            # Try to get agent context (this is tricky, may need thread-local storage)
            agent_context = getattr(self, '_agent_context', None)

            if not agent_context:
                # No context, execute without instrumentation
                return await func(self, *args, **kwargs)

            # Create LLM context
            llm_context = LLMContext(
                model_name=kwargs.get('model', model_name),
                prompt=str(prompt)[:1000],  # Truncate for logging
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 4096),
                start_time=time.time()
            )

            await plugin_manager.trigger_llm_start(agent_context, llm_context)

            response = None
            error = None
            try:
                response = await func(self, *args, **kwargs)
                return response
            except Exception as e:
                error = e
                raise
            finally:
                token_usage = {}  # TODO: Extract from response
                await plugin_manager.trigger_llm_end(
                    agent_context,
                    llm_context,
                    str(response) if response else "",
                    token_usage,
                    error
                )

        return wrapper
    return decorator
