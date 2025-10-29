"""
Plugin Manager

Manages plugin registration, activation/deactivation, and hook execution.
Implements singleton pattern to ensure global consistency.
"""

import asyncio
from typing import Dict, List, Optional
from contextlib import asynccontextmanager
import logging

from .plugin_base import BasePlugin, AgentContext, NodeContext, LLMContext, ToolContext

logger = logging.getLogger(__name__)


class PluginManager:
    """Plugin Manager (Singleton pattern)"""

    _instance: Optional['PluginManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._plugins: Dict[str, BasePlugin] = {}
        self._enabled_plugins: Dict[str, BasePlugin] = {}
        self._hook_handlers: Dict[str, List[BasePlugin]] = {
            'on_agent_start': [],
            'on_agent_end': [],
            'on_node_start': [],
            'on_node_end': [],
            'on_llm_start': [],
            'on_llm_end': [],
            'on_tool_call': [],
            'on_state_update': [],
            'on_error': []
        }
        self._initialized = True
        logger.info("PluginManager initialized")

    def register_plugin(self, plugin: BasePlugin) -> None:
        """Register a plugin"""
        metadata = plugin.metadata
        plugin_id = metadata.id

        if plugin_id in self._plugins:
            logger.warning(f"Plugin {plugin_id} already registered, replacing...")

        self._plugins[plugin_id] = plugin

        if plugin.config.enabled:
            self.enable_plugin(plugin_id)

        logger.info(f"Registered plugin: {metadata.name} v{metadata.version}")

    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister a plugin"""
        if plugin_id in self._enabled_plugins:
            self.disable_plugin(plugin_id)

        if plugin_id in self._plugins:
            plugin = self._plugins.pop(plugin_id)
            asyncio.create_task(plugin.cleanup())
            logger.info(f"Unregistered plugin: {plugin_id}")

    def enable_plugin(self, plugin_id: str) -> None:
        """Enable a plugin"""
        if plugin_id not in self._plugins:
            raise ValueError(f"Plugin {plugin_id} not registered")

        plugin = self._plugins[plugin_id]
        self._enabled_plugins[plugin_id] = plugin

        # Add to hook handler lists
        for hook_name in self._hook_handlers.keys():
            if hasattr(plugin, hook_name):
                self._hook_handlers[hook_name].append(plugin)

        # Sort by priority
        for handlers in self._hook_handlers.values():
            handlers.sort(key=lambda p: p.config.priority)

        logger.info(f"Enabled plugin: {plugin_id}")

    def disable_plugin(self, plugin_id: str) -> None:
        """Disable a plugin"""
        if plugin_id not in self._enabled_plugins:
            return

        plugin = self._enabled_plugins.pop(plugin_id)

        # Remove from hook handler lists
        for handlers in self._hook_handlers.values():
            if plugin in handlers:
                handlers.remove(plugin)

        logger.info(f"Disabled plugin: {plugin_id}")

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """Get plugin instance"""
        return self._plugins.get(plugin_id)

    def get_active_plugins(self) -> List[BasePlugin]:
        """Get all active plugins"""
        return list(self._enabled_plugins.values())

    # ===== Hook trigger methods =====

    async def trigger_agent_start(self, context: AgentContext) -> None:
        """Trigger on_agent_start hook"""
        await self._trigger_hook('on_agent_start', context)

    async def trigger_agent_end(
        self,
        context: AgentContext,
        result: any,
        error: Optional[Exception] = None
    ) -> None:
        """Trigger on_agent_end hook"""
        await self._trigger_hook('on_agent_end', context, result, error=error)

    async def trigger_node_start(self, agent_context: AgentContext, node_context: NodeContext) -> None:
        """Trigger on_node_start hook"""
        await self._trigger_hook('on_node_start', agent_context, node_context)

    async def trigger_node_end(
        self,
        agent_context: AgentContext,
        node_context: NodeContext,
        output_state: Dict,
        error: Optional[Exception] = None
    ) -> None:
        """Trigger on_node_end hook"""
        await self._trigger_hook(
            'on_node_end',
            agent_context,
            node_context,
            output_state,
            error=error
        )

    async def trigger_llm_start(self, agent_context: AgentContext, llm_context: LLMContext) -> None:
        """Trigger on_llm_start hook"""
        await self._trigger_hook('on_llm_start', agent_context, llm_context)

    async def trigger_llm_end(
        self,
        agent_context: AgentContext,
        llm_context: LLMContext,
        response: str,
        token_usage: Dict[str, int],
        error: Optional[Exception] = None
    ) -> None:
        """Trigger on_llm_end hook"""
        await self._trigger_hook(
            'on_llm_end',
            agent_context,
            llm_context,
            response,
            token_usage,
            error=error
        )

    async def trigger_tool_call(
        self,
        agent_context: AgentContext,
        tool_context: ToolContext,
        result: any,
        error: Optional[Exception] = None
    ) -> None:
        """Trigger on_tool_call hook"""
        await self._trigger_hook(
            'on_tool_call',
            agent_context,
            tool_context,
            result,
            error=error
        )

    async def trigger_state_update(
        self,
        agent_context: AgentContext,
        old_state: Dict,
        new_state: Dict
    ) -> None:
        """Trigger on_state_update hook"""
        await self._trigger_hook(
            'on_state_update',
            agent_context,
            old_state,
            new_state
        )

    async def trigger_error(
        self,
        agent_context: AgentContext,
        error: Exception,
        error_context: Dict
    ) -> None:
        """Trigger on_error hook"""
        await self._trigger_hook(
            'on_error',
            agent_context,
            error,
            error_context
        )

    async def _trigger_hook(self, hook_name: str, *args, **kwargs) -> None:
        """Generic hook trigger method"""
        handlers = self._hook_handlers.get(hook_name, [])

        tasks = []
        for plugin in handlers:
            if not plugin.should_process():
                continue

            try:
                handler = getattr(plugin, hook_name)
                if plugin.config.async_mode:
                    # Execute asynchronously, don't block main flow
                    tasks.append(asyncio.create_task(
                        self._safe_execute(handler, *args, **kwargs)
                    ))
                else:
                    # Execute synchronously
                    await self._safe_execute(handler, *args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error triggering {hook_name} on plugin {plugin.metadata.id}: {e}",
                    exc_info=True
                )

        # Wait for all async tasks (but don't block too long)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_execute(self, handler, *args, **kwargs):
        """Safely execute hook handler (catch exceptions)"""
        try:
            await handler(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in plugin hook: {e}", exc_info=True)

    @asynccontextmanager
    async def agent_context(self, context: AgentContext):
        """Agent context manager"""
        await self.trigger_agent_start(context)
        result = None
        error = None
        try:
            yield
        except Exception as e:
            error = e
            raise
        finally:
            await self.trigger_agent_end(context, result, error)


# Global singleton
plugin_manager = PluginManager()
