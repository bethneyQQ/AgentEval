# AgentEval Usage Examples

This document provides examples of how to use the new Model Adapter Factory and Enhanced Metrics Engine.

## Table of Contents

1. [Model Adapter Factory](#model-adapter-factory)
2. [Enhanced Metrics Engine](#enhanced-metrics-engine)
3. [Complete Evaluation Example](#complete-evaluation-example)

---

## Model Adapter Factory

### Basic Usage

```python
from core.model_adapter_factory import ModelAdapterFactory
from core.model_adapter_base import Message

# Initialize factory (will load config/models.yaml)
factory = ModelAdapterFactory()

# List available models
models = factory.list_models()
print(f"Available models: {list(models.keys())}")

# Get a model adapter
adapter = factory.get_adapter("gpt-4-turbo")

# Generate response
messages = [Message(role="user", content="Write a Python function to calculate factorial")]
response = await adapter.generate(messages, temperature=0.0, max_tokens=1024)

print(f"Response: {response.content}")
print(f"Cost: ${response.cost:.4f}")
print(f"Latency: {response.latency:.2f}s")
```

### Using Different Models

```python
# Compare multiple models
models_to_compare = ["gpt-4-turbo", "claude-3-opus", "qwen-max"]

for model_name in models_to_compare:
    adapter = factory.get_adapter(model_name)
    response = await adapter.generate(messages)
    print(f"{model_name}: {response.content[:100]}...")
```

### Custom Model Configuration

Add your own model to `config/models.yaml`:

```yaml
my-custom-model:
  adapter_type: litellm
  model_name: custom/model-id
  provider: custom-provider
  api_key: ${MY_API_KEY}
  api_base: https://api.example.com/v1
  max_input_tokens: 32000
  max_output_tokens: 4096
  pricing:
    input_per_1m: 1.0
    output_per_1m: 2.0
```

Then use it:

```python
adapter = factory.get_adapter("my-custom-model")
```

---

## Enhanced Metrics Engine

### Basic Usage

```python
from core.enhanced_metrics import EnhancedMetricsEngine
from dataclasses import dataclass

@dataclass
class EvaluationResult:
    passed: bool
    execution_time: float
    score: float

# Initialize engine
engine = EnhancedMetricsEngine()

# Create some results
results = [
    EvaluationResult(passed=True, execution_time=1.2, score=0.9),
    EvaluationResult(passed=False, execution_time=2.5, score=0.4),
    EvaluationResult(passed=True, execution_time=1.8, score=0.85),
]

# Calculate all metrics
all_metrics = engine.calculate_all_metrics(results)

for category, metrics in all_metrics.items():
    print(f"\n{category.upper()} Metrics:")
    for metric in metrics:
        print(f"  {metric.name}: {metric.value:.2f} {metric.unit}")
```

### Registering Custom Metrics

#### Method 1: Using Decorator

```python
from core.enhanced_metrics import global_metrics_engine as engine

@engine.metric("success_score", category="quality", description="Combined success and score metric", unit="")
def calculate_success_score(results):
    """Calculate average score for successful tasks only."""
    successful = [r for r in results if r.passed]
    if not successful:
        return 0.0
    return sum(r.score for r in successful) / len(successful)

# Now use it
result = engine.calculate_metric("success_score", results)
print(f"Success Score: {result.value:.2f}")
```

#### Method 2: Direct Registration

```python
def error_rate(results):
    if not results:
        return 0.0
    failed = sum(1 for r in results if not r.passed)
    return (failed / len(results)) * 100.0

engine.register_metric(
    "error_rate",
    error_rate,
    category="basic",
    description="Percentage of failed tasks",
    unit="%"
)
```

### Advanced Custom Metrics

```python
@engine.metric("p95_latency", category="operational", unit="s")
def calculate_p95_latency(results):
    """Calculate 95th percentile latency."""
    import statistics
    times = [r.execution_time for r in results if hasattr(r, 'execution_time')]
    if not times:
        return 0.0
    sorted_times = sorted(times)
    index = int(len(sorted_times) * 0.95)
    return sorted_times[index]

@engine.metric("score_variance", category="quality")
def calculate_score_variance(results):
    """Calculate variance in scores."""
    import statistics
    scores = [r.score for r in results if hasattr(r, 'score')]
    if len(scores) < 2:
        return 0.0
    return statistics.variance(scores)
```

### Filtering Metrics by Category

```python
# Calculate only basic metrics
basic_metrics = engine.calculate_all_metrics(results, categories=["basic"])

# Calculate operational and quality metrics
perf_metrics = engine.calculate_all_metrics(results, categories=["operational", "quality"])
```

### Listing Available Metrics

```python
# List all metrics
all_metric_names = engine.list_metrics()
print(f"All metrics: {all_metric_names}")

# List by category
basic_metrics = engine.list_metrics(category="basic")
print(f"Basic metrics: {basic_metrics}")

custom_metrics = engine.list_metrics(category="custom")
print(f"Custom metrics: {custom_metrics}")
```

---

## Complete Evaluation Example

Here is a complete example combining both components:

```python
import asyncio
from core.model_adapter_factory import ModelAdapterFactory
from core.model_adapter_base import Message
from core.enhanced_metrics import EnhancedMetricsEngine
from dataclasses import dataclass
from typing import List
import time

@dataclass
class TaskResult:
    task_id: str
    passed: bool
    execution_time: float
    score: float
    model_name: str

async def evaluate_model_on_tasks(model_name: str, tasks: List[str]) -> List[TaskResult]:
    """Evaluate a model on a list of tasks."""
    factory = ModelAdapterFactory()
    adapter = factory.get_adapter(model_name)

    results = []
    for i, task in enumerate(tasks):
        start_time = time.time()

        messages = [Message(role="user", content=task)]
        response = await adapter.generate(messages, temperature=0.0)

        execution_time = time.time() - start_time

        # Simple evaluation: check if response is not empty
        passed = len(response.content) > 10
        score = 0.8 if passed else 0.2

        results.append(TaskResult(
            task_id=f"task-{i}",
            passed=passed,
            execution_time=execution_time,
            score=score,
            model_name=model_name
        ))

    return results

async def main():
    # Define test tasks
    tasks = [
        "Write a Python function to check if a number is prime",
        "Create a function to reverse a string",
        "Implement binary search in Python",
    ]

    # Evaluate multiple models
    models = ["gpt-4-turbo", "claude-3-sonnet"]
    all_results = {}

    for model in models:
        print(f"\nEvaluating {model}...")
        results = await evaluate_model_on_tasks(model, tasks)
        all_results[model] = results

    # Calculate metrics for each model
    engine = EnhancedMetricsEngine()

    # Add a custom metric for this evaluation
    @engine.metric("avg_score", category="quality")
    def avg_score(results):
        return sum(r.score for r in results) / len(results) if results else 0.0

    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)

    for model, results in all_results.items():
        print(f"\nModel: {model}")
        print("-" * 40)

        metrics = engine.calculate_all_metrics(results)

        for category, metric_list in metrics.items():
            print(f"\n{category.upper()}:")
            for metric in metric_list:
                print(f"  {metric.name}: {metric.value:.2f} {metric.unit}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Environment Setup

Before running the examples, make sure to set up your environment variables:

```bash
# Create .env file
cat > .env << 'EOF'
# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key

# Alibaba DashScope (Qwen)
DASHSCOPE_API_KEY=your-dashscope-api-key

# DeepSeek
DEEPSEEK_API_KEY=your-deepseek-api-key
EOF

# Load environment variables
export $(cat .env | xargs)
```

Or use python-dotenv:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Next Steps

- Explore the [Design Documentation](design/Milestone1_Offline_Evaluation_Engine_Design.md)
- Check out the [Configuration Examples](design/Milestone1_Configuration_Examples.md)
- Read the [Quick Start Guide](design/Milestone1_Quick_Start.md)
