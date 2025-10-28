# AgentEval Examples

This directory contains example scripts demonstrating how to use the AgentEval system.

## Available Examples

### baseline_evaluation.py

Demonstrates how to run baseline evaluations to establish performance benchmarks.

**Features:**
- Evaluates multiple models on the same benchmark
- Generates comparison reports
- Exports results in multiple formats
- Provides performance metrics

**Usage:**
```bash
python examples/baseline_evaluation.py
```

**Note:** This is a demonstration script. To run actual evaluations, you need:
1. Valid API keys configured (OpenAI, Anthropic, etc.)
2. Access to benchmark datasets
3. Sufficient compute resources

## Quick Start Example

Here's a minimal example to get started:

```python
import asyncio
from core.batch_orchestrator import BatchOrchestrator, EvaluationRequest

async def simple_evaluation():
    # Create evaluation request
    request = EvaluationRequest(
        model_name="gpt-4-turbo",
        benchmark_name="lm_eval",
        max_samples=5,
        output_dir="./results"
    )

    # Create orchestrator and run
    orchestrator = BatchOrchestrator(max_concurrent=3)
    result = await orchestrator.run_evaluation(request)

    # Print results
    print(f"Pass rate: {result.summary['pass_rate']:.2%}")
    print(f"Average score: {result.summary['average_score']:.4f}")

# Run
asyncio.run(simple_evaluation())
```

## Using the CLI

The easiest way to run evaluations is using the CLI:

```bash
# Basic evaluation
python cli/evaluate.py --model gpt-4-turbo --benchmark lm_eval --max-samples 10

# With specific task
python cli/evaluate.py \
  --model gpt-4-turbo \
  --benchmark lm_eval \
  --task single_turn_scenarios_function_generation \
  --max-samples 5

# With custom settings
python cli/evaluate.py \
  --model gpt-4-turbo \
  --benchmark lm_eval \
  --max-samples 10 \
  --max-concurrent 5 \
  --temperature 0.0 \
  --output-dir ./my_results \
  --export html csv json

# List available resources
python cli/list_resources.py models
python cli/list_resources.py benchmarks
```

## Configuration

### Model Configuration

Models are configured in `config/models.yaml`. Example:

```yaml
models:
  gpt-4-turbo:
    provider: openai
    model_id: gpt-4-turbo-preview
    api_key_env: OPENAI_API_KEY

  claude-3-opus:
    provider: anthropic
    model_id: claude-3-opus-20240229
    api_key_env: ANTHROPIC_API_KEY
```

### Environment Variables

Set API keys as environment variables:

```bash
export OPENAI_API_KEY=your_openai_key
export ANTHROPIC_API_KEY=your_anthropic_key
```

## Advanced Usage

### Custom Metrics

```python
from core.enhanced_metrics import metric, EnhancedMetricsEngine

# Define custom metric
@metric(category="custom", name="code_quality")
def calculate_code_quality(results):
    # Your custom logic
    return 0.95

# Use with orchestrator
engine = EnhancedMetricsEngine()
engine.register_metric(calculate_code_quality)

orchestrator = BatchOrchestrator(metrics_engine=engine)
```

### Custom Export

```python
from core.export_handlers import HTMLExporter, CSVExporter

# Export results
html_exporter = HTMLExporter()
html_exporter.export(result, "report.html")

csv_exporter = CSVExporter()
csv_exporter.export(result, "results.csv")
```

## Performance Tips

1. **Concurrency**: Use `--max-concurrent` to control parallelism
2. **Batch Size**: Process tasks in batches for better throughput
3. **Output Format**: Use CSV for large datasets (faster than HTML)
4. **Progress Tracking**: Use `--no-progress` to disable for automated runs

## Troubleshooting

### API Rate Limits

If you encounter rate limit errors, reduce concurrency:

```bash
python cli/evaluate.py --model gpt-4-turbo --benchmark lm_eval --max-concurrent 1
```

### Memory Issues

For large evaluations, process in smaller batches:

```bash
python cli/evaluate.py --model gpt-4-turbo --benchmark lm_eval --max-samples 10
```

## Support

For issues and questions:
- Check the main README.md
- Review test files for usage examples
- See API documentation in docs/
