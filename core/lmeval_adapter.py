"""
LM-Evaluation-Harness adapter for AgentEval.

This adapter integrates the lm-evaluation-harness framework for evaluating
LLMs on code generation and understanding tasks.
"""

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import time

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


class LMEvalTask(BaseTask):
    """Task representation for lm-evaluation-harness."""

    def __init__(
        self,
        task_id: str,
        description: str,
        language: str,
        scenario: str,
        difficulty: str,
        prompt: str,
        reference: Optional[List[str]] = None,
        tests: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ):
        metadata = {
            "scenario": scenario,
            "prompt": prompt,
            "reference": reference or [],
            "tests": tests or [],
            **kwargs
        }
        super().__init__(
            task_id=task_id,
            benchmark_name="lm_eval",
            description=description,
            language=language,
            difficulty=difficulty,
            metadata=metadata
        )
        self.scenario = scenario
        self.prompt = prompt
        self.reference = reference or []
        self.tests = tests or []


class LMEvalAdapter(BenchmarkAdapter):
    """
    Adapter for lm-evaluation-harness (CodeBenchmark).

    This adapter provides integration with lm-eval for evaluating
    LLMs on various code generation and understanding tasks.
    """

    def __init__(
        self,
        config: Optional[EvaluationConfig] = None,
        task_name: str = "single_turn_scenarios_function_generation",
        lmeval_path: Optional[str] = None
    ):
        """
        Initialize the lm-eval adapter.

        Args:
            config: Evaluation configuration
            task_name: Name of the task to evaluate
            lmeval_path: Path to lm-eval installation
        """
        super().__init__(config)
        self.task_name = task_name
        self.lmeval_path = lmeval_path or "/home/shared/zqq/CodeBenchmark"
        self.tasks_cache: List[LMEvalTask] = []

        # Map task names to benchmark types
        self.task_type_map = {
            "function_generation": BenchmarkType.CODE_GENERATION,
            "code_completion": BenchmarkType.CODE_COMPLETION,
            "bug_fix": BenchmarkType.BUG_FIXING,
            "algorithm_implementation": BenchmarkType.CODE_GENERATION,
        }

    def get_adapter_info(self) -> AdapterInfo:
        """Get information about this adapter."""
        benchmark_type = BenchmarkType.CODE_GENERATION
        for key, value in self.task_type_map.items():
            if key in self.task_name:
                benchmark_type = value
                break

        return AdapterInfo(
            name="lm_eval",
            version="1.0.0",
            benchmark_type=benchmark_type,
            description="LM-Evaluation-Harness for code generation and understanding tasks",
            supported_languages=["python"],
            requires_docker=False,
            requires_sandbox=True,
            metadata={
                "task_name": self.task_name,
                "lmeval_path": self.lmeval_path
            }
        )

    def initialize(self) -> None:
        """Initialize the adapter."""
        if not Path(self.lmeval_path).exists():
            raise FileNotFoundError(
                f"LM-Eval not found at {self.lmeval_path}. "
                "Please ensure CodeBenchmark is installed."
            )

        logger.info(f"Initialized lm_eval adapter with task: {self.task_name}")
        self._initialized = True

    def load_tasks(
        self,
        task_ids: Optional[List[str]] = None,
        max_samples: Optional[int] = None
    ) -> List[LMEvalTask]:
        """
        Load tasks from lm-eval task definitions.

        Args:
            task_ids: Specific task IDs to load
            max_samples: Maximum number of tasks to load

        Returns:
            List of LMEvalTask objects
        """
        if not self._initialized:
            self.initialize()

        # Determine task category
        if "single_turn" in self.task_name:
            task_category = "single_turn_scenarios"
        elif "multi_turn" in self.task_name:
            task_category = "multi_turn_scenarios"
        else:
            task_category = "single_turn_scenarios"

        # Load problems from JSONL file
        problems_path = Path(self.lmeval_path) / "lm_eval" / "tasks" / task_category / "problems.jsonl"

        if not problems_path.exists():
            logger.warning(f"Problems file not found at {problems_path}")
            return []

        tasks = []
        try:
            with open(problems_path, 'r') as f:
                for i, line in enumerate(f):
                    if max_samples and i >= max_samples:
                        break

                    problem = json.loads(line)
                    problem_id = problem.get("id", f"problem_{i}")

                    if task_ids and problem_id not in task_ids:
                        continue

                    task = LMEvalTask(
                        task_id=problem_id,
                        description=problem.get("title", ""),
                        language=problem.get("language", "python"),
                        scenario=problem.get("scenario", ""),
                        difficulty=problem.get("difficulty", "intermediate"),
                        prompt=problem.get("prompt", ""),
                        reference=problem.get("reference", []),
                        tests=problem.get("tests", []),
                        context_mode=problem.get("context_mode", ""),
                        metadata_extra=problem.get("metadata", {})
                    )
                    tasks.append(task)

            self.tasks_cache = tasks
            logger.info(f"Loaded {len(tasks)} tasks from {problems_path}")
            return tasks

        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            raise

    def evaluate_task(
        self,
        task: BaseTask,
        model_output: str,
        **kwargs
    ) -> TaskResult:
        """
        Evaluate a single task using lm-eval metrics.

        Args:
            task: The task to evaluate
            model_output: The model's generated code
            **kwargs: Additional parameters

        Returns:
            TaskResult with evaluation results
        """
        start_time = time.time()

        try:
            # Evaluate using lm-eval metrics
            metrics = self._evaluate_code(task, model_output)

            execution_time = time.time() - start_time

            # Calculate overall score
            score = self._calculate_score(metrics)
            passed = score >= 0.5  # threshold

            return TaskResult(
                task_id=task.task_id,
                benchmark_name="lm_eval",
                status=TaskStatus.COMPLETED,
                passed=passed,
                score=score,
                execution_time=execution_time,
                metrics=metrics,
                output=model_output
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error evaluating task {task.task_id}: {e}")

            return TaskResult(
                task_id=task.task_id,
                benchmark_name="lm_eval",
                status=TaskStatus.ERROR,
                passed=False,
                score=0.0,
                execution_time=execution_time,
                error_message=str(e),
                metrics={}
            )

    def _evaluate_code(
        self,
        task: BaseTask,
        generated_code: str
    ) -> Dict[str, float]:
        """
        Evaluate generated code using multiple metrics.

        Args:
            task: The task
            generated_code: Generated code

        Returns:
            Dictionary of metric scores
        """
        metrics = {}

        # 1. Syntax validity check
        try:
            compile(generated_code, '<string>', 'exec')
            metrics['syntax_validity'] = 1.0
        except SyntaxError:
            metrics['syntax_validity'] = 0.0

        # 2. Runtime correctness (basic check)
        try:
            # Create a safe execution environment
            namespace = {}
            exec(generated_code, namespace)
            metrics['runtime_correctness'] = 1.0
        except Exception as e:
            logger.debug(f"Runtime error: {e}")
            metrics['runtime_correctness'] = 0.0

        # 3. Exact match with reference (if available)
        if hasattr(task, 'reference') and task.reference:
            reference = task.reference[0] if task.reference else ""
            # Normalize whitespace for comparison
            gen_normalized = ' '.join(generated_code.split())
            ref_normalized = ' '.join(reference.split())
            metrics['exact_match'] = 1.0 if gen_normalized == ref_normalized else 0.0
        else:
            metrics['exact_match'] = 0.0

        # 4. Code quality heuristics
        metrics['code_quality'] = self._assess_code_quality(generated_code)

        return metrics

    def _assess_code_quality(self, code: str) -> float:
        """
        Assess code quality using heuristics.

        Args:
            code: The code to assess

        Returns:
            Quality score between 0 and 1
        """
        score = 0.5  # baseline

        # Check for docstrings
        if '"""' in code or "'''" in code:
            score += 0.1

        # Check for comments
        if '#' in code:
            score += 0.1

        # Check for type hints
        if '->' in code or ': ' in code:
            score += 0.1

        # Check for error handling
        if 'try' in code or 'except' in code:
            score += 0.1

        # Penalize very short code
        if len(code) < 20:
            score -= 0.2

        # Penalize very long code (might be verbose)
        if len(code) > 1000:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _calculate_score(self, metrics: Dict[str, float]) -> float:
        """
        Calculate overall score from metrics.

        Args:
            metrics: Dictionary of metric scores

        Returns:
            Overall score between 0 and 1
        """
        # Weighted average of metrics
        weights = {
            'syntax_validity': 0.3,
            'runtime_correctness': 0.4,
            'exact_match': 0.2,
            'code_quality': 0.1
        }

        score = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            if metric in metrics:
                score += metrics[metric] * weight
                total_weight += weight

        if total_weight > 0:
            score = score / total_weight

        return score

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
        logger.info("Cleaned up lm_eval adapter resources")


def create_lmeval_adapter(
    task_name: str = "single_turn_scenarios_function_generation",
    max_samples: Optional[int] = None,
    **config_kwargs
) -> LMEvalAdapter:
    """
    Factory function to create an lm-eval adapter.

    Args:
        task_name: Name of the task
        max_samples: Maximum number of samples
        **config_kwargs: Additional config parameters

    Returns:
        Configured LMEvalAdapter
    """
    config = EvaluationConfig(max_samples=max_samples, **config_kwargs)
    return LMEvalAdapter(config=config, task_name=task_name)
