"""
Plugin Base Classes and Interfaces

This module defines the core interfaces for the AgentEval plugin system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field


class PluginMetadata(BaseModel):
    """Plugin metadata"""
    id: str  # Unique identifier
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = Field(default_factory=list)  # Dependencies on other plugins


class PluginConfig(BaseModel):
    """Plugin configuration"""
    enabled: bool = True
    priority: int = 100  # Priority (lower number = higher priority)
    sampling_rate: float = 1.0  # Sampling rate (0.0-1.0)
    async_mode: bool = True  # Whether to execute asynchronously
    extra: Dict[str, Any] = Field(default_factory=dict)  # Extra configuration


class AgentContext(BaseModel):
    """Agent execution context"""
    agent_id: str
    agent_type: str  # DevAgent, ChatAgent, etc.
    agent_version: str
    session_id: str
    user_id: str
    task_id: str
    workspace_path: str
    start_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NodeContext(BaseModel):
    """Node execution context"""
    node_name: str
    start_time: float
    input_state: Dict[str, Any] = Field(default_factory=dict)


class LLMContext(BaseModel):
    """LLM call context"""
    model_name: str
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 4096
    start_time: float


class ToolContext(BaseModel):
    """Tool call context"""
    tool_name: str
    tool_input: Dict[str, Any] = Field(default_factory=dict)
    start_time: float


class BasePlugin(ABC):
    """Base plugin class

    All plugins must inherit from this class and implement the metadata property.
    Plugins can override lifecycle hooks to collect and process agent execution data.
    """

    def __init__(self, config: Optional[PluginConfig] = None):
        self.config = config or PluginConfig()
        self._enabled = self.config.enabled

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass

    # ===== Lifecycle hooks =====

    async def on_agent_start(self, context: AgentContext) -> None:
        """Triggered when agent starts"""
        pass

    async def on_agent_end(
        self,
        context: AgentContext,
        result: Any,
        error: Optional[Exception] = None
    ) -> None:
        """Triggered when agent ends"""
        pass

    async def on_node_start(
        self,
        agent_context: AgentContext,
        node_context: NodeContext
    ) -> None:
        """Triggered when node starts"""
        pass

    async def on_node_end(
        self,
        agent_context: AgentContext,
        node_context: NodeContext,
        output_state: Dict[str, Any],
        error: Optional[Exception] = None
    ) -> None:
        """Triggered when node ends"""
        pass

    async def on_llm_start(
        self,
        agent_context: AgentContext,
        llm_context: LLMContext
    ) -> None:
        """Triggered when LLM call starts"""
        pass

    async def on_llm_end(
        self,
        agent_context: AgentContext,
        llm_context: LLMContext,
        response: str,
        token_usage: Dict[str, int],
        error: Optional[Exception] = None
    ) -> None:
        """Triggered when LLM call ends"""
        pass

    async def on_tool_call(
        self,
        agent_context: AgentContext,
        tool_context: ToolContext,
        result: Any,
        error: Optional[Exception] = None
    ) -> None:
        """Triggered when tool is called"""
        pass

    async def on_state_update(
        self,
        agent_context: AgentContext,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any]
    ) -> None:
        """Triggered when state is updated"""
        pass

    async def on_error(
        self,
        agent_context: AgentContext,
        error: Exception,
        error_context: Dict[str, Any]
    ) -> None:
        """Triggered when error occurs"""
        pass

    # ===== Helper methods =====

    def should_process(self) -> bool:
        """Determine if this event should be processed (considering sampling rate)"""
        if not self._enabled:
            return False

        if self.config.sampling_rate >= 1.0:
            return True

        import random
        return random.random() < self.config.sampling_rate

    async def cleanup(self) -> None:
        """Clean up resources (called when plugin is unloaded)"""
        pass
