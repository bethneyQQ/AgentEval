# Benchmark Adapters Guide

This guide explains how to use the benchmark adapter framework to integrate different benchmarking systems into AgentEval.

## Overview

AgentEval now supports integration with multiple benchmarking frameworks through a unified adapter interface:
- **loombenchmark** (SWE-bench fork) - for GitHub issue resolution tasks
- **lm-evaluation-harness** (CodeBenchmark) - for code generation and understanding tasks

## Quick Start

### 1. List Available Adapters

```python
from core.benchmark_registry import list_adapters

adapters = list_adapters()
print(f"Available adapters: {adapters}")
# Output: ['loombench', 'lm_eval']
```

### 2. Get Adapter Information

```python
from core.benchmark_registry import get_adapter_info

# Get information about lm_eval adapter
info = get_adapter_info("lm_eval")
print(f"Name: {info['name']}")
print(f"Version: {info['version']}")
print(f"Type: {info['benchmark_type']}")
print(f"Description: {info['description']}")
```

### 3. Use an Adapter

#### LM-Eval Adapter (Code Generation Tasks)

```python
from core.benchmark_registry import get_adapter
from core.benchmark_adapter_base import EvaluationConfig

# Create configuration
config = EvaluationConfig(
    max_samples=10,
    timeout=300,
    temperature=0.0
)

# Get lm_eval adapter
adapter = get_adapter(
    "lm_eval",
    config=config,
    task_name="single_turn_scenarios_function_generation"
)

# Initialize and load tasks
with adapter:
    tasks = adapter.load_tasks(max_samples=5)

    print(f"Loaded {len(tasks)} tasks")

    # Evaluate a task
    task = tasks[0]
    model_output = "def hello():\n    print('Hello World')"

    result = adapter.evaluate_task(task, model_output)

    print(f"Task: {result.task_id}")
    print(f"Passed: {result.passed}")
    print(f"Score: {result.score:.2f}")
    print(f"Metrics: {result.metrics}")
```

#### LoomBench Adapter (GitHub Issue Resolution)

```python
from core.benchmark_registry import get_adapter

# Get loombench adapter
adapter = get_adapter(
    "loombench",
    dataset_name="princeton-nlp/SWE-bench_Lite"
)

# Initialize and load tasks
with adapter:
    tasks = adapter.load_tasks(max_samples=3)

    print(f"Loaded {len(tasks)} tasks")

    # Evaluate a task
    task = tasks[0]
    patch = """
diff --git a/file.py b/file.py
index 123..456 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,3 @@
-def buggy():
+def fixed():
    pass
"""

    result = adapter.evaluate_task(task, patch)

    print(f"Task: {result.task_id}")
    print(f"Resolved: {result.passed}")
    print(f"Execution time: {result.execution_time:.2f}s")
```

## Complete Evaluation Example

Here's a complete example that combines the Model Adapter Factory with Benchmark Adapters:

```python
import asyncio
from core.model_adapter_factory import ModelAdapterFactory
from core.model_adapter_base import Message
from core.benchmark_registry import get_adapter
from core.benchmark_adapter_base import EvaluationConfig

async def evaluate_model_on_benchmark():
    """Evaluate a model on a benchmark."""

    # 1. Set up model adapter
    model_factory = ModelAdapterFactory()
    model_adapter = model_factory.get_adapter("gpt-4-turbo")

    # 2. Set up benchmark adapter
    config = EvaluationConfig(max_samples=5, temperature=0.0)
    benchmark_adapter = get_adapter(
        "lm_eval",
        config=config,
        task_name="single_turn_scenarios_function_generation"
    )

    # 3. Load tasks
    with benchmark_adapter:
        tasks = benchmark_adapter.load_tasks(max_samples=5)

        results = []
        for task in tasks:
            # Generate code using the model
            messages = [Message(role="user", content=task.metadata["prompt"])]
            response = await model_adapter.generate(messages, temperature=0.0)

            # Evaluate the generated code
            result = benchmark_adapter.evaluate_task(task, response.content)
            results.append(result)

            print(f"Task {result.task_id}: "
                  f"{'PASSED' if result.passed else 'FAILED'} "
                  f"(score: {result.score:.2f})")

        # Calculate overall metrics
        total_tasks = len(results)
        passed_tasks = sum(1 for r in results if r.passed)
        avg_score = sum(r.score for r in results) / total_tasks
        avg_time = sum(r.execution_time for r in results) / total_tasks

        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        print(f"Total tasks: {total_tasks}")
        print(f"Passed: {passed_tasks} ({passed_tasks/total_tasks*100:.1f}%)")
        print(f"Average score: {avg_score:.3f}")
        print(f"Average execution time: {avg_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(evaluate_model_on_benchmark())
```

## Available Task Types

### LM-Eval Tasks

Single-turn scenarios:
- `single_turn_scenarios_function_generation` - Generate complete functions
- `single_turn_scenarios_code_completion` - Complete partial code
- `single_turn_scenarios_bug_fix` - Fix buggy code
- `single_turn_scenarios_algorithm_implementation` - Implement algorithms
- `single_turn_scenarios_api_design` - Design API interfaces
- `single_turn_scenarios_system_design` - System architecture design

Multi-turn scenarios:
- `multi_turn_scenarios_project_development` - Full project development
- `multi_turn_scenarios_code_review` - Code review processes
- `multi_turn_scenarios_debugging_session` - Interactive debugging

### LoomBench Datasets

- `princeton-nlp/SWE-bench_Lite` - Lite version (300 instances)
- `princeton-nlp/SWE-bench` - Full version (2,294 instances)

## Evaluation Metrics

### LM-Eval Metrics

- **syntax_validity**: Code is syntactically valid (0.0-1.0)
- **runtime_correctness**: Code executes without errors (0.0-1.0)
- **exact_match**: Exact match with reference solution (0.0-1.0)
- **code_quality**: Heuristic-based quality score (0.0-1.0)

### LoomBench Metrics

- **resolved**: Whether the issue was resolved (boolean)
- **test_result**: Detailed test execution results

## Configuration Options

### EvaluationConfig

```python
from core.benchmark_adapter_base import EvaluationConfig

config = EvaluationConfig(
    max_samples=10,         # Maximum number of tasks to evaluate
    timeout=300,            # Timeout per task (seconds)
    num_workers=1,          # Number of parallel workers
    temperature=0.0,        # Model temperature
    max_tokens=4096,        # Maximum tokens to generate
    batch_size=1,           # Batch size for evaluation
    enable_caching=True,    # Enable result caching
    custom_params={}        # Additional custom parameters
)
```

## Creating Custom Adapters

You can create your own benchmark adapters by subclassing `BenchmarkAdapter`:

```python
from core.benchmark_adapter_base import (
    BenchmarkAdapter,
    AdapterInfo,
    BaseTask,
    TaskResult,
    BenchmarkType,
    TaskStatus,
    EvaluationConfig
)

class MyCustomAdapter(BenchmarkAdapter):
    """Custom benchmark adapter."""

    def get_adapter_info(self) -> AdapterInfo:
        return AdapterInfo(
            name="my_custom",
            version="1.0.0",
            benchmark_type=BenchmarkType.CUSTOM,
            description="My custom benchmark",
            supported_languages=["python"],
            requires_docker=False,
            requires_sandbox=False
        )

    def initialize(self) -> None:
        # Initialize your benchmark
        self._initialized = True

    def load_tasks(self, task_ids=None, max_samples=None):
        # Load tasks from your benchmark
        tasks = []
        # ... your loading logic ...
        return tasks

    def evaluate_task(self, task, model_output, **kwargs):
        # Evaluate a single task
        # ... your evaluation logic ...
        return TaskResult(
            task_id=task.task_id,
            benchmark_name="my_custom",
            status=TaskStatus.COMPLETED,
            passed=True,
            score=1.0,
            execution_time=0.5
        )

    def evaluate_batch(self, tasks, model_outputs, **kwargs):
        # Evaluate a batch of tasks
        return [
            self.evaluate_task(task, output, **kwargs)
            for task, output in zip(tasks, model_outputs)
        ]

# Register your adapter
from core.benchmark_registry import global_adapter_registry
global_adapter_registry.register("my_custom", MyCustomAdapter)
```

## Best Practices

1. **Use context managers**: Always use adapters with context managers (`with` statement) to ensure proper cleanup

2. **Handle errors gracefully**: Adapters handle errors and return TaskResult with ERROR status

3. **Limit samples for testing**: Use `max_samples` parameter when testing to avoid long evaluation times

4. **Cache results**: Enable caching in EvaluationConfig to avoid re-evaluating the same tasks

5. **Monitor resource usage**: Some benchmarks (especially loombench) require significant resources (Docker, storage)

## Troubleshooting

### LM-Eval Issues

**Problem**: Tasks file not found
```
FileNotFoundError: problems.jsonl not found
```
**Solution**: Ensure CodeBenchmark is installed at `/home/shared/zqq/CodeBenchmark`

### LoomBench Issues

**Problem**: datasets library not installed
```
ImportError: datasets library not installed
```
**Solution**: Install datasets: `pip install datasets`

**Problem**: Docker not available
```
Error: Docker is required for loombench evaluation
```
**Solution**: Install and start Docker daemon

## Testing

Run the benchmark adapter tests:

```bash
# Run all tests
python -m pytest tests/test_benchmark_adapters.py -v

# Run specific test class
python -m pytest tests/test_benchmark_adapters.py::TestLMEvalAdapter -v

# Run with coverage
python -m pytest tests/test_benchmark_adapters.py --cov=core --cov-report=html
```

## Next Steps

- Integrate adapters with Batch Orchestrator for parallel evaluation
- Add more benchmark adapters (e.g., HumanEval, MBPP)
- Implement result caching and persistence
- Create CLI tools for easy evaluation

## References

- [Benchmark Adapter Base Classes](../core/benchmark_adapter_base.py)
- [LoomBench Adapter](../core/loombench_adapter.py)
- [LM-Eval Adapter](../core/lmeval_adapter.py)
- [Benchmark Registry](../core/benchmark_registry.py)
