# Quick Start: New Features

This guide shows you how to use the new Model Adapter Factory and Enhanced Metrics Engine.

## Installation

```bash
# Install required dependencies
pip install litellm pyyaml python-dotenv

# Set up environment variables
export OPENAI_API_KEY=your-openai-key
export ANTHROPIC_API_KEY=your-anthropic-key
export DASHSCOPE_API_KEY=your-qwen-key
export DEEPSEEK_API_KEY=your-deepseek-key
```

## Feature 1: Model Adapter Factory

Use any of 10+ LLM models with a unified interface:

```python
import asyncio
from core.model_adapter_factory import ModelAdapterFactory
from core.model_adapter_base import Message

async def main():
    # Initialize factory
    factory = ModelAdapterFactory()

    # List available models
    print("Available models:", list(factory.list_models().keys()))

    # Use a model
    adapter = factory.get_adapter("gpt-4-turbo")

    # Generate response
    messages = [Message(role="user", content="Write a Python function to calculate factorial")]
    response = await adapter.generate(messages, temperature=0.0)

    print(f"Response: {response.content}")
    print(f"Cost: ${response.cost:.4f}")
    print(f"Tokens: {response.usage}")

asyncio.run(main())
```

### Supported Models

- OpenAI: gpt-4-turbo, gpt-4o, gpt-3.5-turbo
- Anthropic: claude-3-opus, claude-3-sonnet, claude-3-haiku
- Alibaba: qwen-max, qwen-plus
- DeepSeek: deepseek-chat, deepseek-coder

### Adding Your Own Model

Edit `config/models.yaml`:

```yaml
my-model:
  adapter_type: litellm
  model_name: provider/model-id
  provider: my-provider
  api_key: ${MY_API_KEY}
  max_input_tokens: 32000
  max_output_tokens: 4096
  pricing:
    input_per_1m: 1.0
    output_per_1m: 3.0
```

## Feature 2: Enhanced Metrics Engine

Easy-to-extend metrics calculation:

```python
from core.enhanced_metrics import EnhancedMetricsEngine
from dataclasses import dataclass

@dataclass
class Result:
    passed: bool
    execution_time: float
    score: float

# Initialize engine
engine = EnhancedMetricsEngine()

# Define custom metric with decorator
@engine.metric("success_score", category="quality", unit="")
def calculate_success_score(results):
    successful = [r for r in results if r.passed]
    if not successful:
        return 0.0
    return sum(r.score for r in successful) / len(successful)

# Create results
results = [
    Result(passed=True, execution_time=1.2, score=0.9),
    Result(passed=False, execution_time=2.5, score=0.4),
    Result(passed=True, execution_time=1.8, score=0.85),
]

# Calculate all metrics
all_metrics = engine.calculate_all_metrics(results)

# Print results
for category, metrics in all_metrics.items():
    print(f"\n{category.upper()}:")
    for metric in metrics:
        print(f"  {metric.name}: {metric.value:.2f} {metric.unit}")
```

### Built-in Metrics

- total_tasks: Count of all tasks
- pass_rate: Percentage of passed tasks
- avg_execution_time: Average execution time

### Adding Custom Metrics

Method 1: Decorator
```python
@engine.metric("my_metric", category="custom")
def my_metric(results):
    return sum(r.score for r in results) / len(results)
```

Method 2: Direct registration
```python
def my_metric(results):
    return len(results) * 2

engine.register_metric("double_count", my_metric, category="custom")
```

## Running Tests

```bash
# Test Model Adapter Factory
python -m pytest tests/test_model_adapter.py -v

# Test Enhanced Metrics Engine
python -m pytest tests/test_enhanced_metrics.py -v

# Run all tests
python -m pytest tests/ -v
```

## Complete Example

See `docs/USAGE_EXAMPLES.md` for a complete example that combines both features
to evaluate multiple models on multiple tasks and calculate comprehensive metrics.

## Documentation

- [Usage Examples](docs/USAGE_EXAMPLES.md) - Detailed usage examples
- [Progress Report](docs/MILESTONE1_PROGRESS.md) - Development progress and architecture decisions
- [Design Documents](docs/design/) - Complete design documentation

## Key Features

1. **Model Adapter Factory**
   - Unified interface for 10+ LLM providers
   - Configuration-driven (no code changes)
   - Automatic cost calculation
   - Environment variable support

2. **Enhanced Metrics Engine**
   - Easy custom metric definition
   - Decorator-based registration
   - Category-based organization
   - Built-in common metrics

3. **Integration**
   - Works alongside existing code
   - Backward compatible
   - Well tested (20 tests, all passing)
   - Comprehensive documentation

## Next Steps

1. Explore the full API in `docs/USAGE_EXAMPLES.md`
2. Read the design documentation in `docs/design/`
3. Check out existing benchmark adapters in `core/`
4. Integrate with your evaluation workflows
