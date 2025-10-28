"""
Batch Orchestrator for parallel evaluation of multiple tasks.

This module provides functionality to orchestrate large-scale evaluations
with concurrent task execution, progress tracking, and result aggregation.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from pathlib import Path
import json

from core.model_adapter_factory import ModelAdapterFactory
from core.model_adapter_base import Message, ModelAdapter
from core.benchmark_adapter_base import (
    BenchmarkAdapter,
    BaseTask,
    TaskResult,
    TaskStatus,
    EvaluationConfig
)
from core.benchmark_registry import get_adapter
from core.enhanced_metrics import EnhancedMetricsEngine, MetricResult

logger = logging.getLogger(__name__)


@dataclass
class EvaluationRequest:
    """Request for running an evaluation."""
    model_name: str
    benchmark_name: str
    task_name: Optional[str] = None
    max_samples: Optional[int] = None
    config: Optional[EvaluationConfig] = None
    model_config: Optional[Dict[str, Any]] = None
    benchmark_config: Optional[Dict[str, Any]] = None
    output_dir: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of a complete evaluation run."""
    request: EvaluationRequest
    task_results: List[TaskResult]
    metrics: Dict[str, MetricResult]
    summary: Dict[str, Any]
    start_time: datetime
    end_time: datetime
    total_time: float
    error: Optional[str] = None


class BatchOrchestrator:
    """
    Orchestrator for batch evaluation of tasks.

    This class manages the entire evaluation pipeline including:
    - Loading tasks from benchmarks
    - Generating model outputs
    - Evaluating outputs
    - Calculating metrics
    - Progress tracking
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        enable_progress: bool = True,
        metrics_engine: Optional[EnhancedMetricsEngine] = None
    ):
        """
        Initialize the batch orchestrator.

        Args:
            max_concurrent: Maximum number of concurrent tasks
            enable_progress: Whether to show progress information
            metrics_engine: Custom metrics engine. If None, creates a new one.
        """
        self.max_concurrent = max_concurrent
        self.enable_progress = enable_progress
        self.metrics_engine = metrics_engine or EnhancedMetricsEngine()

        self.model_factory = ModelAdapterFactory()

    async def run_evaluation(
        self,
        request: EvaluationRequest,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> EvaluationResult:
        """
        Run a complete evaluation.

        Args:
            request: The evaluation request
            progress_callback: Optional callback for progress updates.
                Receives (completed_tasks, total_tasks) as arguments.

        Returns:
            EvaluationResult with complete results

        Example:
            request = EvaluationRequest(
                model_name="gpt-4-turbo",
                benchmark_name="lm_eval",
                task_name="single_turn_scenarios_function_generation",
                max_samples=10
            )
            result = await orchestrator.run_evaluation(request)
        """
        start_time = datetime.now()
        logger.info(f"Starting evaluation: {request.model_name} on {request.benchmark_name}")

        try:
            # 1. Load model adapter
            model_adapter = self.model_factory.get_adapter(request.model_name)
            logger.info(f"Loaded model: {request.model_name}")

            # 2. Load benchmark adapter
            config = request.config or EvaluationConfig(max_samples=request.max_samples)
            benchmark_kwargs = request.benchmark_config or {}

            if request.task_name:
                benchmark_kwargs['task_name'] = request.task_name

            benchmark_adapter = get_adapter(
                request.benchmark_name,
                config=config,
                **benchmark_kwargs
            )
            logger.info(f"Loaded benchmark: {request.benchmark_name}")

            # 3. Load tasks
            with benchmark_adapter:
                tasks = benchmark_adapter.load_tasks(
                    max_samples=request.max_samples or config.max_samples
                )
                logger.info(f"Loaded {len(tasks)} tasks")

                if not tasks:
                    raise ValueError("No tasks loaded from benchmark")

                # 4. Execute tasks concurrently
                task_results = await self._execute_tasks_concurrent(
                    tasks=tasks,
                    model_adapter=model_adapter,
                    benchmark_adapter=benchmark_adapter,
                    config=config,
                    progress_callback=progress_callback
                )

            # 5. Calculate metrics
            metrics = self.metrics_engine.calculate_all_metrics(task_results)

            # 6. Generate summary
            summary = self._generate_summary(task_results, metrics)

            # 7. Save results if output_dir specified
            if request.output_dir:
                self._save_results(
                    request,
                    task_results,
                    metrics,
                    summary,
                    request.output_dir
                )

            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()

            logger.info(
                f"Evaluation completed in {total_time:.2f}s. "
                f"Pass rate: {summary['pass_rate']:.2%}"
            )

            return EvaluationResult(
                request=request,
                task_results=task_results,
                metrics=metrics,
                summary=summary,
                start_time=start_time,
                end_time=end_time,
                total_time=total_time
            )

        except Exception as e:
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()

            logger.error(f"Evaluation failed: {e}")

            return EvaluationResult(
                request=request,
                task_results=[],
                metrics={},
                summary={},
                start_time=start_time,
                end_time=end_time,
                total_time=total_time,
                error=str(e)
            )

    async def _execute_tasks_concurrent(
        self,
        tasks: List[BaseTask],
        model_adapter: ModelAdapter,
        benchmark_adapter: BenchmarkAdapter,
        config: EvaluationConfig,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[TaskResult]:
        """
        Execute tasks concurrently with semaphore control.

        Args:
            tasks: List of tasks to execute
            model_adapter: Model adapter to use
            benchmark_adapter: Benchmark adapter for evaluation
            config: Evaluation configuration
            progress_callback: Optional progress callback

        Returns:
            List of task results
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        completed = 0
        total = len(tasks)

        async def execute_with_semaphore(task: BaseTask) -> TaskResult:
            nonlocal completed

            async with semaphore:
                result = await self._execute_single_task(
                    task, model_adapter, benchmark_adapter, config
                )

                completed += 1

                if self.enable_progress:
                    logger.info(f"Progress: {completed}/{total} tasks completed")

                if progress_callback:
                    progress_callback(completed, total)

                return result

        # Execute all tasks concurrently
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=False
        )

        return results

    async def _execute_single_task(
        self,
        task: BaseTask,
        model_adapter: ModelAdapter,
        benchmark_adapter: BenchmarkAdapter,
        config: EvaluationConfig
    ) -> TaskResult:
        """
        Execute a single task.

        Args:
            task: The task to execute
            model_adapter: Model adapter to use
            benchmark_adapter: Benchmark adapter for evaluation
            config: Evaluation configuration

        Returns:
            TaskResult
        """
        try:
            # 1. Get prompt from task
            prompt = task.metadata.get('prompt', task.description)

            # 2. Generate model output
            messages = [Message(role="user", content=prompt)]
            response = await model_adapter.generate(
                messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )

            # 3. Evaluate the output
            result = benchmark_adapter.evaluate_task(
                task,
                response.content,
                model_name=model_adapter.get_model_info().name
            )

            return result

        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")

            # Return error result
            return TaskResult(
                task_id=task.task_id,
                benchmark_name=task.benchmark_name,
                status=TaskStatus.ERROR,
                passed=False,
                score=0.0,
                execution_time=0.0,
                error_message=str(e),
                metrics={}
            )

    def _generate_summary(
        self,
        task_results: List[TaskResult],
        metrics: Dict[str, List[MetricResult]]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics.

        Args:
            task_results: List of task results
            metrics: Calculated metrics by category

        Returns:
            Dictionary with summary statistics
        """
        total_tasks = len(task_results)
        passed_tasks = sum(1 for r in task_results if r.passed)
        failed_tasks = sum(1 for r in task_results if not r.passed and r.status != TaskStatus.ERROR)
        error_tasks = sum(1 for r in task_results if r.status == TaskStatus.ERROR)

        avg_score = sum(r.score for r in task_results) / total_tasks if total_tasks > 0 else 0.0
        avg_time = sum(r.execution_time for r in task_results) / total_tasks if total_tasks > 0 else 0.0

        # Extract key metrics
        key_metrics = {}
        for category, metric_list in metrics.items():
            for metric in metric_list:
                key_metrics[f"{category}_{metric.name}"] = metric.value

        return {
            "total_tasks": total_tasks,
            "passed_tasks": passed_tasks,
            "failed_tasks": failed_tasks,
            "error_tasks": error_tasks,
            "pass_rate": passed_tasks / total_tasks if total_tasks > 0 else 0.0,
            "average_score": avg_score,
            "average_execution_time": avg_time,
            "metrics": key_metrics
        }

    def _save_results(
        self,
        request: EvaluationRequest,
        task_results: List[TaskResult],
        metrics: Dict[str, List[MetricResult]],
        summary: Dict[str, Any],
        output_dir: str
    ) -> None:
        """
        Save evaluation results to disk.

        Args:
            request: The evaluation request
            task_results: List of task results
            metrics: Calculated metrics
            summary: Summary statistics
            output_dir: Output directory path
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{request.model_name}_{request.benchmark_name}_{timestamp}"

        # Save summary
        summary_file = output_path / f"{base_filename}_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({
                "request": {
                    "model_name": request.model_name,
                    "benchmark_name": request.benchmark_name,
                    "task_name": request.task_name,
                    "max_samples": request.max_samples,
                    "metadata": request.metadata
                },
                "summary": summary,
                "timestamp": timestamp
            }, f, indent=2)

        logger.info(f"Saved summary to {summary_file}")

        # Save detailed results
        results_file = output_path / f"{base_filename}_results.jsonl"
        with open(results_file, 'w') as f:
            for result in task_results:
                f.write(json.dumps({
                    "task_id": result.task_id,
                    "benchmark_name": result.benchmark_name,
                    "status": result.status.value,
                    "passed": result.passed,
                    "score": result.score,
                    "execution_time": result.execution_time,
                    "error_message": result.error_message,
                    "metrics": result.metrics,
                    "timestamp": result.timestamp.isoformat()
                }) + '\n')

        logger.info(f"Saved {len(task_results)} results to {results_file}")
