"""
Tests for Model Adapter Factory and related components.
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from core.model_adapter_base import (
    ModelAdapter, Message, Tool, GenerateResponse,
    ModelInfo, ModelCapability
)
from core.model_adapter_factory import ModelAdapterFactory


class TestModelAdapterFactory:
    """Tests for ModelAdapterFactory."""

    def test_factory_initialization(self):
        """Test factory initialization without config file."""
        factory = ModelAdapterFactory(config_path="nonexistent.yaml")
        models = factory.list_models()
        assert isinstance(models, dict)

    def test_factory_with_config(self, tmp_path):
        """Test factory with valid configuration."""
        config_file = tmp_path / "test_models.yaml"
        config_content = """
models:
  test-model:
    adapter_type: litellm
    model_name: gpt-3.5-turbo
    provider: openai
    api_key: test-key
    max_input_tokens: 4096
    max_output_tokens: 2048
    pricing:
      input_per_1m: 0.5
      output_per_1m: 1.5
"""
        config_file.write_text(config_content)

        factory = ModelAdapterFactory(config_path=str(config_file))
        models = factory.list_models()

        assert "test-model" in models
        assert models["test-model"]["provider"] == "openai"

    def test_env_var_expansion(self, tmp_path, monkeypatch):
        """Test environment variable expansion in config."""
        monkeypatch.setenv("TEST_API_KEY", "my-secret-key")

        config_file = tmp_path / "test_models.yaml"
        config_content = """
models:
  test-model:
    adapter_type: litellm
    model_name: gpt-3.5-turbo
    provider: openai
    api_key: ${TEST_API_KEY}
    max_input_tokens: 4096
    max_output_tokens: 2048
    pricing:
      input_per_1m: 0.5
      output_per_1m: 1.5
"""
        config_file.write_text(config_content)

        factory = ModelAdapterFactory(config_path=str(config_file))
        models = factory.list_models()

        assert models["test-model"]["api_key"] == "my-secret-key"

    def test_get_unknown_model(self, tmp_path):
        """Test getting an unknown model raises ValueError."""
        config_file = tmp_path / "test_models.yaml"
        config_file.write_text("models: {}")

        factory = ModelAdapterFactory(config_path=str(config_file))

        with pytest.raises(ValueError, match="not found"):
            factory.get_adapter("unknown-model")

    def test_adapter_caching(self, tmp_path):
        """Test that adapters are cached."""
        config_file = tmp_path / "test_models.yaml"
        config_content = """
models:
  test-model:
    adapter_type: litellm
    model_name: gpt-3.5-turbo
    provider: openai
    api_key: test-key
    max_input_tokens: 4096
    max_output_tokens: 2048
    pricing:
      input_per_1m: 0.5
      output_per_1m: 1.5
"""
        config_file.write_text(config_content)

        factory = ModelAdapterFactory(config_path=str(config_file))

        adapter1 = factory.get_adapter("test-model")
        adapter2 = factory.get_adapter("test-model")

        assert adapter1 is adapter2


class TestModelAdapter:
    """Tests for ModelAdapter base class."""

    def test_message_creation(self):
        """Test Message dataclass creation."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_tool_creation(self):
        """Test Tool dataclass creation."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object"}
        )
        assert tool.name == "test_tool"

    def test_generate_response_creation(self):
        """Test GenerateResponse creation."""
        response = GenerateResponse(
            content="Hello world",
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 20}
        )
        assert response.content == "Hello world"
        assert response.timestamp is not None

    def test_cost_calculation(self):
        """Test cost calculation."""
        class MockAdapter(ModelAdapter):
            def get_model_info(self):
                return ModelInfo(
                    name="test",
                    provider="test",
                    capabilities=[ModelCapability.TEXT_GENERATION],
                    max_input_tokens=4096,
                    max_output_tokens=2048,
                    pricing={"input_per_1m": 1.0, "output_per_1m": 3.0}
                )

            async def generate(self, messages, tools=None, temperature=0.7, max_tokens=4096, **kwargs):
                pass

        adapter = MockAdapter({})
        usage = {"prompt_tokens": 1000, "completion_tokens": 2000}
        cost = adapter.calculate_cost(usage)

        expected_cost = (1000 / 1_000_000) * 1.0 + (2000 / 1_000_000) * 3.0
        assert abs(cost - expected_cost) < 0.0001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
