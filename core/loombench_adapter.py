"""
Loombenchmark (SWE-bench) adapter for AgentEval.

This adapter integrates the loombenchmark framework for evaluating
LLMs on real-world software engineering tasks.
"""

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import os

from core.benchmark_adapter_base import (
    AdapterInfo,
    BaseTask,
    BenchmarkAdapter,
    BenchmarkType,
    EvaluationConfig,
    TaskResult,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class LoomBenchTask(BaseTask):
    """Task representation for loombenchmark."""

    def __init__(
        self,
        task_id: str,
        description: str,
        language: str = "python",
        repo: Optional[str] = None,
        base_commit: Optional[str] = None,
        test_patch: Optional[str] = None,
        problem_statement: Optional[str] = None,
        hints_text: Optional[str] = None,
        **kwargs
    ):
        metadata = {
            "repo": repo,
            "base_commit": base_commit,
            "test_patch": test_patch,
            "problem_statement": problem_statement,
            "hints_text": hints_text,
            **kwargs
        }
        super().__init__(
            task_id=task_id,
            benchmark_name="loombench",
            description=description or problem_statement or "",
            language=language,
            metadata=metadata
        )
        self.repo = repo
        self.base_commit = base_commit
        self.test_patch = test_patch
        self.problem_statement = problem_statement


class LoomBenchAdapter(BenchmarkAdapter):
    """
    Adapter for loombenchmark (SWE-bench fork).

    This adapter provides integration with loombenchmark for evaluating
    LLMs on GitHub issue resolution tasks.
    """

    def __init__(
        self,
        config: Optional[EvaluationConfig] = None,
        dataset_name: str = "princeton-nlp/SWE-bench_Lite",
        loombench_path: Optional[str] = None
    ):
        """
        Initialize the loombenchmark adapter.

        Args:
            config: Evaluation configuration
            dataset_name: Name of the dataset to use
            loombench_path: Path to loombenchmark installation
        """
        super().__init__(config)
        self.dataset_name = dataset_name
        self.loombench_path = loombench_path or "/home/shared/zqq/loombenchmark"
        self.tasks_cache: List[LoomBenchTask] = []

    def get_adapter_info(self) -> AdapterInfo:
        """Get information about this adapter."""
        return AdapterInfo(
            name="loombench",
            version="2.0.0",
            benchmark_type=BenchmarkType.ISSUE_RESOLUTION,
            description="SWE-bench fork for evaluating LLMs on GitHub issue resolution",
            supported_languages=["python"],
            requires_docker=True,
            requires_sandbox=True,
            metadata={
                "dataset": self.dataset_name,
                "loombench_path": self.loombench_path
            }
        )

    def initialize(self) -> None:
        """Initialize the adapter."""
        if not Path(self.loombench_path).exists():
            raise FileNotFoundError(
                f"Loombenchmark not found at {self.loombench_path}. "
                "Please ensure loombenchmark is installed."
            )

        logger.info(f"Initialized loombench adapter with dataset: {self.dataset_name}")
        self._initialized = True

    def load_tasks(
        self,
        task_ids: Optional[List[str]] = None,
        max_samples: Optional[int] = None
    ) -> List[LoomBenchTask]:
        """
        Load tasks from loombenchmark dataset.

        Args:
            task_ids: Specific task IDs to load
            max_samples: Maximum number of tasks to load

        Returns:
            List of LoomBenchTask objects
        """
        if not self._initialized:
            self.initialize()

        # Try to load from HuggingFace datasets
        try:
            from datasets import load_dataset
            dataset = load_dataset(self.dataset_name, split="test")

            tasks = []
            for i, instance in enumerate(dataset):
                if max_samples and i >= max_samples:
                    break

                instance_id = instance.get("instance_id", f"task_{i}")

                if task_ids and instance_id not in task_ids:
                    continue

                task = LoomBenchTask(
                    task_id=instance_id,
                    description=instance.get("problem_statement", ""),
                    language="python",
                    repo=instance.get("repo", ""),
                    base_commit=instance.get("base_commit", ""),
                    test_patch=instance.get("test_patch", ""),
                    problem_statement=instance.get("problem_statement", ""),
                    hints_text=instance.get("hints_text", ""),
                )
                tasks.append(task)

            self.tasks_cache = tasks
            logger.info(f"Loaded {len(tasks)} tasks from {self.dataset_name}")
            return tasks

        except ImportError:
            logger.error("datasets library not installed. Install with: pip install datasets")
            raise
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            raise

    def evaluate_task(
        self,
        task: BaseTask,
        model_output: str,
        **kwargs
    ) -> TaskResult:
        """
        Evaluate a single task using loombenchmark.

        Args:
            task: The task to evaluate
            model_output: The model's prediction (patch)
            **kwargs: Additional parameters

        Returns:
            TaskResult with evaluation results
        """
        import time
        start_time = time.time()

        try:
            # Create predictions file
            prediction = {
                "instance_id": task.task_id,
                "model_name_or_path": kwargs.get("model_name", "unknown"),
                "model_patch": model_output,
            }

            # Write predictions to temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.jsonl',
                delete=False
            ) as f:
                f.write(json.dumps(prediction) + '\n')
                pred_file = f.name

            try:
                # Run loombench evaluation
                # Note: This is a simplified version. In production, you would
                # use loombench.harness.run_evaluation directly
                result = self._run_evaluation(pred_file, task)

                execution_time = time.time() - start_time

                return TaskResult(
                    task_id=task.task_id,
                    benchmark_name="loombench",
                    status=TaskStatus.COMPLETED,
                    passed=result.get("resolved", False),
                    score=1.0 if result.get("resolved", False) else 0.0,
                    execution_time=execution_time,
                    metrics={
                        "resolved": result.get("resolved", False),
                        "test_result": result.get("test_result", {}),
                    },
                    output=model_output
                )

            finally:
                # Clean up temp file
                if os.path.exists(pred_file):
                    os.unlink(pred_file)

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error evaluating task {task.task_id}: {e}")

            return TaskResult(
                task_id=task.task_id,
                benchmark_name="loombench",
                status=TaskStatus.ERROR,
                passed=False,
                score=0.0,
                execution_time=execution_time,
                error_message=str(e),
                metrics={}
            )

    def _run_evaluation(
        self,
        predictions_path: str,
        task: BaseTask
    ) -> Dict[str, Any]:
        """
        Run loombenchmark evaluation.

        Args:
            predictions_path: Path to predictions file
            task: The task being evaluated

        Returns:
            Dictionary with evaluation results
        """
        # Import loombenchmark modules
        try:
            # Add loombench to path if not already there
            import sys
            if self.loombench_path not in sys.path:
                sys.path.insert(0, self.loombench_path)

            # This is a placeholder for the actual evaluation logic
            # In production, you would integrate with loombench.harness.run_evaluation
            # For now, we return a mock result
            logger.warning(
                "Using mock evaluation. "
                "Implement actual loombench evaluation for production use."
            )

            return {
                "resolved": False,
                "test_result": {
                    "status": "mock",
                    "message": "Mock evaluation - implement actual loombench integration"
                }
            }

        except Exception as e:
            logger.error(f"Error running loombench evaluation: {e}")
            raise

    def evaluate_batch(
        self,
        tasks: List[BaseTask],
        model_outputs: List[str],
        **kwargs
    ) -> List[TaskResult]:
        """
        Evaluate a batch of tasks.

        Args:
            tasks: List of tasks to evaluate
            model_outputs: List of model outputs
            **kwargs: Additional parameters

        Returns:
            List of TaskResult objects
        """
        if len(tasks) != len(model_outputs):
            raise ValueError(
                f"Number of tasks ({len(tasks)}) must match "
                f"number of outputs ({len(model_outputs)})"
            )

        results = []
        for task, output in zip(tasks, model_outputs):
            result = self.evaluate_task(task, output, **kwargs)
            results.append(result)

        return results

    def cleanup(self) -> None:
        """Clean up resources."""
        self.tasks_cache = []
        logger.info("Cleaned up loombench adapter resources")


def create_loombench_adapter(
    dataset_name: str = "princeton-nlp/SWE-bench_Lite",
    max_samples: Optional[int] = None,
    **config_kwargs
) -> LoomBenchAdapter:
    """
    Factory function to create a loombench adapter.

    Args:
        dataset_name: Name of the dataset
        max_samples: Maximum number of samples
        **config_kwargs: Additional config parameters

    Returns:
        Configured LoomBenchAdapter
    """
    config = EvaluationConfig(max_samples=max_samples, **config_kwargs)
    return LoomBenchAdapter(config=config, dataset_name=dataset_name)
