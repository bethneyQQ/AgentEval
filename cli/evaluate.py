#!/usr/bin/env python3
"""
Command-line interface for running evaluations.

This script provides a CLI for evaluating models on various benchmarks
and exporting results in different formats.
"""

import argparse
import asyncio
import sys
import logging
from pathlib import Path
from typing import Optional

from core.batch_orchestrator import (
    BatchOrchestrator,
    EvaluationRequest,
    EvaluationConfig
)
from core.export_handlers import HTMLExporter, CSVExporter, JSONExporter


def setup_logging(verbose: bool = False) -> None:
    """
    Setup logging configuration.

    Args:
        verbose: Whether to enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Evaluate AI models on various benchmarks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run GPT-4 on LM Eval benchmark
  %(prog)s --model gpt-4-turbo --benchmark lm_eval --max-samples 10

  # Run evaluation with specific task
  %(prog)s --model gpt-4-turbo --benchmark lm_eval \\
           --task single_turn_scenarios_function_generation --max-samples 5

  # Run with custom output directory and export formats
  %(prog)s --model gpt-4-turbo --benchmark lm_eval --max-samples 10 \\
           --output-dir ./results --export html csv json

  # Run with more concurrent tasks
  %(prog)s --model gpt-4-turbo --benchmark lm_eval --max-samples 20 \\
           --max-concurrent 10
        """
    )

    # Required arguments
    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Model name (e.g., gpt-4-turbo, claude-3-opus-20240229)'
    )

    parser.add_argument(
        '--benchmark',
        type=str,
        required=True,
        help='Benchmark name (e.g., lm_eval, loombench)'
    )

    # Optional arguments
    parser.add_argument(
        '--task',
        type=str,
        help='Specific task name within the benchmark'
    )

    parser.add_argument(
        '--max-samples',
        type=int,
        default=None,
        help='Maximum number of samples to evaluate'
    )

    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=5,
        help='Maximum number of concurrent task executions (default: 5)'
    )

    parser.add_argument(
        '--temperature',
        type=float,
        default=0.0,
        help='Temperature for model generation (default: 0.0)'
    )

    parser.add_argument(
        '--max-tokens',
        type=int,
        default=2048,
        help='Maximum tokens for model generation (default: 2048)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='./eval_results',
        help='Output directory for results (default: ./eval_results)'
    )

    parser.add_argument(
        '--export',
        type=str,
        nargs='+',
        choices=['html', 'csv', 'json'],
        default=['html', 'json'],
        help='Export formats (default: html json)'
    )

    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress reporting'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser.parse_args()


def progress_callback(completed: int, total: int) -> None:
    """
    Progress callback for evaluation.

    Args:
        completed: Number of completed tasks
        total: Total number of tasks
    """
    percentage = (completed / total) * 100 if total > 0 else 0
    print(f"Progress: {completed}/{total} tasks completed ({percentage:.1f}%)")


async def run_evaluation(args: argparse.Namespace) -> int:
    """
    Run the evaluation.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Create evaluation config
        config = EvaluationConfig(
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            max_samples=args.max_samples
        )

        # Create evaluation request
        request = EvaluationRequest(
            model_name=args.model,
            benchmark_name=args.benchmark,
            task_name=args.task,
            max_samples=args.max_samples,
            config=config,
            output_dir=args.output_dir
        )

        # Create orchestrator
        orchestrator = BatchOrchestrator(
            max_concurrent=args.max_concurrent,
            enable_progress=not args.no_progress
        )

        # Run evaluation
        print(f"\nStarting evaluation:")
        print(f"  Model: {args.model}")
        print(f"  Benchmark: {args.benchmark}")
        if args.task:
            print(f"  Task: {args.task}")
        print(f"  Max samples: {args.max_samples or 'all'}")
        print(f"  Max concurrent: {args.max_concurrent}")
        print()

        result = await orchestrator.run_evaluation(
            request,
            progress_callback=progress_callback if not args.no_progress else None
        )

        # Check for errors
        if result.error:
            print(f"\nEvaluation failed: {result.error}", file=sys.stderr)
            return 1

        # Print summary
        print(f"\nEvaluation completed successfully!")
        print(f"  Total time: {result.total_time:.2f}s")
        print(f"  Total tasks: {result.summary.get('total_tasks', 0)}")
        print(f"  Passed tasks: {result.summary.get('passed_tasks', 0)}")
        print(f"  Failed tasks: {result.summary.get('failed_tasks', 0)}")
        print(f"  Error tasks: {result.summary.get('error_tasks', 0)}")
        print(f"  Pass rate: {result.summary.get('pass_rate', 0):.2%}")
        print(f"  Average score: {result.summary.get('average_score', 0):.4f}")

        # Export results
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        base_filename = f"{args.model}_{args.benchmark}"
        if args.task:
            base_filename += f"_{args.task}"

        print(f"\nExporting results to: {output_dir}")

        if 'html' in args.export:
            html_exporter = HTMLExporter()
            html_path = output_dir / f"{base_filename}.html"
            html_exporter.export(result, str(html_path))
            print(f"  HTML report: {html_path}")

        if 'csv' in args.export:
            csv_exporter = CSVExporter()
            csv_path = output_dir / f"{base_filename}.csv"
            csv_exporter.export(result, str(csv_path))
            print(f"  CSV results: {csv_path}")

        if 'json' in args.export:
            json_exporter = JSONExporter()
            json_path = output_dir / f"{base_filename}.json"
            json_exporter.export(result, str(json_path))
            print(f"  JSON results: {json_path}")

        print(f"\nEvaluation complete!")
        return 0

    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        logging.exception("Evaluation failed with exception")
        return 1


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code
    """
    args = parse_args()
    setup_logging(args.verbose)

    return asyncio.run(run_evaluation(args))


if __name__ == "__main__":
    sys.exit(main())
