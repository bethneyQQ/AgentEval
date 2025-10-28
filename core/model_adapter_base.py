"""
Base classes and interfaces for model adapters.

This module provides unified interfaces for integrating different LLM providers
into the evaluation engine.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ModelCapability(Enum):
    """Model capability enumeration."""
    TEXT_GENERATION = "text_generation"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    CODE_GENERATION = "code_generation"


@dataclass
class ModelInfo:
    """Model metadata information."""
    name: str
    provider: str
    capabilities: List[ModelCapability]
    max_input_tokens: int
    max_output_tokens: int
    pricing: Dict[str, float]
    supports_streaming: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """Conversation message."""
    role: str  # system, user, assistant
    content: str


@dataclass
class Tool:
    """Function calling tool definition."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema


@dataclass
class GenerateResponse:
    """Generation response from model."""
    content: str
    finish_reason: str
    tool_calls: Optional[List[Dict]] = None
    usage: Optional[Dict[str, int]] = None  # prompt_tokens, completion_tokens
    cost: Optional[float] = None
    latency: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


class ModelAdapter(ABC):
    """Abstract base class for model adapters."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._client = None

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> GenerateResponse:
        """Generate response from the model."""
        pass

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Get model metadata information."""
        pass

    def calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate cost based on token usage."""
        info = self.get_model_info()
        if 'input_per_1m' not in info.pricing or 'output_per_1m' not in info.pricing:
            return 0.0

        input_cost = (usage.get('prompt_tokens', 0) / 1_000_000) * info.pricing['input_per_1m']
        output_cost = (usage.get('completion_tokens', 0) / 1_000_000) * info.pricing['output_per_1m']
        return input_cost + output_cost


class ModelGenerationError(Exception):
    """Exception raised when model generation fails."""
    pass
