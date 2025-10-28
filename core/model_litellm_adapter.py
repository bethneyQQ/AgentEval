"""
LiteLLM-based model adapter implementation.

This adapter provides a unified interface to 100+ LLM providers through LiteLLM.
"""

import time
import asyncio
from typing import List, Optional, Dict, Any
import logging

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logging.warning("LiteLLM not installed. Install with: pip install litellm")

from .model_adapter_base import (
    ModelAdapter, Message, Tool, GenerateResponse,
    ModelInfo, ModelCapability, ModelGenerationError
)
from .retry_handler import (
    RetryConfig, retry_with_backoff,
    RateLimitError, TimeoutError, ServiceUnavailableError,
    API_RATE_LIMIT_RETRY_CONFIG
)

logger = logging.getLogger(__name__)


class LiteLLMAdapter(ModelAdapter):
    """Model adapter based on LiteLLM with retry support."""

    def __init__(
        self,
        config: Dict[str, Any],
        retry_config: Optional[RetryConfig] = None
    ):
        super().__init__(config)

        if not LITELLM_AVAILABLE:
            raise ImportError("LiteLLM is not installed")

        self.model_name = config['model_name']
        self.api_base = config.get('api_base')
        self.api_key = config.get('api_key')
        self.retry_config = retry_config or API_RATE_LIMIT_RETRY_CONFIG

        if self.api_base:
            litellm.api_base = self.api_base
        if self.api_key:
            litellm.api_key = self.api_key

    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> GenerateResponse:
        """Generate response from LLM with automatic retry on failures."""

        @retry_with_backoff(config=self.retry_config)
        async def _generate_with_retry():
            start_time = time.time()

            litellm_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            litellm_tools = None
            if tools:
                litellm_tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.parameters
                        }
                    }
                    for tool in tools
                ]

            try:
                response = await litellm.acompletion(
                    model=self.model_name,
                    messages=litellm_messages,
                    tools=litellm_tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )

                latency = time.time() - start_time

                choice = response.choices[0]
                content = choice.message.content or ""
                finish_reason = choice.finish_reason

                tool_calls = None
                if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                    tool_calls = [
                        {
                            "id": tc.id,
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                        for tc in choice.message.tool_calls
                    ]

                usage = None
                cost = None
                if hasattr(response, 'usage'):
                    usage = {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    }
                    cost = self.calculate_cost(usage)

                return GenerateResponse(
                    content=content,
                    finish_reason=finish_reason,
                    tool_calls=tool_calls,
                    usage=usage,
                    cost=cost,
                    latency=latency
                )

            except Exception as e:
                # Map LiteLLM exceptions to our retry exceptions
                error_str = str(e).lower()

                if 'rate limit' in error_str or 'too many requests' in error_str:
                    raise RateLimitError(f"Rate limit exceeded: {e}")
                elif 'timeout' in error_str or 'timed out' in error_str:
                    raise TimeoutError(f"Request timed out: {e}")
                elif 'unavailable' in error_str or 'service' in error_str:
                    raise ServiceUnavailableError(f"Service unavailable: {e}")
                else:
                    logger.error(f"Model generation failed: {str(e)}")
                    raise ModelGenerationError(f"Failed to generate response: {str(e)}")

        return await _generate_with_retry()

    def get_model_info(self) -> ModelInfo:
        """Get model information from configuration."""
        return ModelInfo(
            name=self.model_name,
            provider=self.config.get('provider', 'unknown'),
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION
            ],
            max_input_tokens=self.config.get('max_input_tokens', 128000),
            max_output_tokens=self.config.get('max_output_tokens', 4096),
            pricing=self.config.get('pricing', {"input_per_1m": 1.0, "output_per_1m": 3.0}),
            supports_streaming=True
        )
