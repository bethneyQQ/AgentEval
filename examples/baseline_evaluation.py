#!/usr/bin/env python3
"""
Baseline Evaluation Example

This script demonstrates how to run baseline evaluations to establish
performance baselines for different models and benchmarks.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.batch_orchestrator import (
    BatchOrchestrator,
    EvaluationRequest,
    EvaluationConfig
)
from core.export_handlers import HTMLExporter, CSVExporter, JSONExporter


async def run_baseline_evaluation():
    """
    Run baseline evaluations for establishing performance benchmarks.

    This example shows how to evaluate multiple models on a benchmark
    and compare their performance.
    """
    print("=" * 80)
    print("Baseline Evaluation Example")
    print("=" * 80)
    print()

    # Models to evaluate
    models = [
        "gpt-4-turbo",
        "gpt-3.5-turbo",
        "claude-3-sonnet-20240229",
    ]

    # Benchmark configuration
    benchmark_name = "lm_eval"
    task_name = "single_turn_scenarios_function_generation"
    max_samples = 10  # Small sample for demonstration
    output_dir = "./baseline_results"

    # Evaluation configuration
    config = EvaluationConfig(
        temperature=0.0,  # Deterministic for baselines
        max_tokens=2048,
        max_samples=max_samples
    )

    # Create orchestrator
    orchestrator = BatchOrchestrator(
        max_concurrent=3,
        enable_progress=True
    )

    results = {}

    print(f"Running baseline evaluations on {len(models)} models...")
    print(f"Benchmark: {benchmark_name}")
    print(f"Task: {task_name}")
    print(f"Samples: {max_samples}")
    print()

    for model in models:
        print(f"\nEvaluating {model}...")
        print("-" * 80)

        # Create evaluation request
        request = EvaluationRequest(
            model_name=model,
            benchmark_name=benchmark_name,
            task_name=task_name,
            max_samples=max_samples,
            config=config,
            output_dir=output_dir,
            metadata={
                "evaluation_type": "baseline",
                "purpose": "establishing performance benchmarks"
            }
        )

        # Run evaluation
        try:
            result = await orchestrator.run_evaluation(request)

            if result.error:
                print(f"Error evaluating {model}: {result.error}")
                continue

            results[model] = result

            # Print summary
            print(f"\nResults for {model}:")
            print(f"  Total tasks: {result.summary.get('total_tasks', 0)}")
            print(f"  Passed: {result.summary.get('passed_tasks', 0)}")
            print(f"  Failed: {result.summary.get('failed_tasks', 0)}")
            print(f"  Pass rate: {result.summary.get('pass_rate', 0):.2%}")
            print(f"  Average score: {result.summary.get('average_score', 0):.4f}")
            print(f"  Average time: {result.summary.get('average_execution_time', 0):.2f}s")
            print(f"  Total time: {result.total_time:.2f}s")

        except Exception as e:
            print(f"Exception evaluating {model}: {e}")
            continue

    # Generate comparison report
    if results:
        print("\n" + "=" * 80)
        print("Baseline Comparison")
        print("=" * 80)
        print()

        # Sort by pass rate
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1].summary.get('pass_rate', 0),
            reverse=True
        )

        print(f"{'Model':<30} {'Pass Rate':<12} {'Avg Score':<12} {'Avg Time':<12}")
        print("-" * 80)

        for model, result in sorted_results:
            pass_rate = result.summary.get('pass_rate', 0)
            avg_score = result.summary.get('average_score', 0)
            avg_time = result.summary.get('average_execution_time', 0)

            print(f"{model:<30} {pass_rate:>10.2%} {avg_score:>10.4f} {avg_time:>10.2f}s")

        print()

        # Export comparison report
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create comparison summary
        comparison = {
            "evaluation_type": "baseline",
            "benchmark": benchmark_name,
            "task": task_name,
            "max_samples": max_samples,
            "models": [
                {
                    "model_name": model,
                    "pass_rate": result.summary.get('pass_rate', 0),
                    "average_score": result.summary.get('average_score', 0),
                    "average_time": result.summary.get('average_execution_time', 0),
                    "total_tasks": result.summary.get('total_tasks', 0),
                    "passed_tasks": result.summary.get('passed_tasks', 0),
                }
                for model, result in sorted_results
            ]
        }

        # Export as JSON
        import json
        comparison_file = output_path / "baseline_comparison.json"
        with open(comparison_file, 'w') as f:
            json.dump(comparison, f, indent=2)

        print(f"Comparison report saved to: {comparison_file}")

        # Export individual reports
        for model, result in results.items():
            model_safe = model.replace('/', '_').replace('-', '_')

            # HTML report
            html_exporter = HTMLExporter()
            html_file = output_path / f"{model_safe}_baseline.html"
            html_exporter.export(result, str(html_file))
            print(f"HTML report for {model}: {html_file}")

    else:
        print("\nNo successful evaluations completed.")

    print("\n" + "=" * 80)
    print("Baseline evaluation complete!")
    print("=" * 80)


def main():
    """Main entry point."""
    print("\nNOTE: This is a demonstration script.")
    print("To run actual evaluations, you need:")
    print("  1. Valid API keys configured (OpenAI, Anthropic, etc.)")
    print("  2. Access to benchmark datasets")
    print("  3. Sufficient compute resources")
    print()

    try:
        asyncio.run(run_baseline_evaluation())
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
