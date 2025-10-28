"""
Base classes and interfaces for benchmark adapters.

This module provides abstract base classes for integrating different
benchmarking frameworks into the AgentEval system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class TaskStatus(Enum):
    """Status of a task execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


class BenchmarkType(Enum):
    """Type of benchmark."""
    CODE_GENERATION = "code_generation"
    BUG_FIXING = "bug_fixing"
    CODE_COMPLETION = "code_completion"
    ISSUE_RESOLUTION = "issue_resolution"
    MULTI_TURN = "multi_turn"
    CUSTOM = "custom"


@dataclass
class AdapterInfo:
    """Information about a benchmark adapter."""
    name: str
    version: str
    benchmark_type: BenchmarkType
    description: str
    supported_languages: List[str]
    requires_docker: bool = False
    requires_sandbox: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BaseTask:
    """Base task representation."""
    task_id: str
    benchmark_name: str
    description: str
    language: str
    difficulty: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result of a task evaluation."""
    task_id: str
    benchmark_name: str
    status: TaskStatus
    passed: bool
    score: float
    execution_time: float
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    output: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EvaluationConfig:
    """Configuration for benchmark evaluation."""
    max_samples: Optional[int] = None
    timeout: int = 300
    num_workers: int = 1
    temperature: float = 0.0
    max_tokens: int = 4096
    batch_size: int = 1
    enable_caching: bool = True
    custom_params: Dict[str, Any] = field(default_factory=dict)


class UnifiedEnv(ABC):
    """Abstract base class for task execution environments."""

    @abstractmethod
    def setup(self) -> None:
        """Set up the execution environment."""
        pass

    @abstractmethod
    def execute(self, code: str, task: BaseTask) -> TaskResult:
        """
        Execute code in the environment.

        Args:
            code: The code to execute
            task: The task being evaluated

        Returns:
            TaskResult containing execution results
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up the execution environment."""
        pass


class BenchmarkAdapter(ABC):
    """
    Abstract base class for benchmark adapters.

    A benchmark adapter provides a unified interface to interact with
    different benchmarking frameworks (e.g., loombenchmark, lm_eval).
    """

    def __init__(self, config: Optional[EvaluationConfig] = None):
        """
        Initialize the benchmark adapter.

        Args:
            config: Configuration for the benchmark evaluation
        """
        self.config = config or EvaluationConfig()
        self._initialized = False

    @abstractmethod
    def get_adapter_info(self) -> AdapterInfo:
        """
        Get information about this adapter.

        Returns:
            AdapterInfo containing adapter metadata
        """
        pass

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the benchmark adapter.

        This method should load datasets, set up environments, etc.
        """
        pass

    @abstractmethod
    def load_tasks(
        self,
        task_ids: Optional[List[str]] = None,
        max_samples: Optional[int] = None
    ) -> List[BaseTask]:
        """
        Load tasks from the benchmark.

        Args:
            task_ids: Specific task IDs to load. If None, load all tasks.
            max_samples: Maximum number of tasks to load

        Returns:
            List of BaseTask objects
        """
        pass

    @abstractmethod
    def evaluate_task(
        self,
        task: BaseTask,
        model_output: str,
        **kwargs
    ) -> TaskResult:
        """
        Evaluate a single task.

        Args:
            task: The task to evaluate
            model_output: The output from the model
            **kwargs: Additional evaluation parameters

        Returns:
            TaskResult containing evaluation results
        """
        pass

    @abstractmethod
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
            model_outputs: List of model outputs corresponding to tasks
            **kwargs: Additional evaluation parameters

        Returns:
            List of TaskResult objects
        """
        pass

    def cleanup(self) -> None:
        """
        Clean up resources used by the adapter.

        Override this method if your adapter needs cleanup.
        """
        pass

    def __enter__(self):
        """Context manager entry."""
        if not self._initialized:
            self.initialize()
            self._initialized = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False


class BenchmarkAdapterRegistry:
    """Registry for benchmark adapters."""

    def __init__(self):
        self._adapters: Dict[str, type] = {}

    def register(self, name: str, adapter_class: type) -> None:
        """
        Register a benchmark adapter.

        Args:
            name: Name of the adapter
            adapter_class: The adapter class (subclass of BenchmarkAdapter)
        """
        if not issubclass(adapter_class, BenchmarkAdapter):
            raise TypeError(
                f"Adapter class must be a subclass of BenchmarkAdapter, "
                f"got {adapter_class}"
            )

        self._adapters[name] = adapter_class

    def get_adapter(
        self,
        name: str,
        config: Optional[EvaluationConfig] = None
    ) -> BenchmarkAdapter:
        """
        Get a benchmark adapter by name.

        Args:
            name: Name of the adapter
            config: Configuration for the adapter

        Returns:
            Instance of the requested adapter

        Raises:
            KeyError: If adapter not found
        """
        if name not in self._adapters:
            raise KeyError(
                f"Adapter '{name}' not found. "
                f"Available adapters: {list(self._adapters.keys())}"
            )

        adapter_class = self._adapters[name]
        return adapter_class(config=config)

    def list_adapters(self) -> List[str]:
        """
        List all registered adapters.

        Returns:
            List of adapter names
        """
        return list(self._adapters.keys())

    def get_adapter_info(self, name: str) -> AdapterInfo:
        """
        Get information about an adapter.

        Args:
            name: Name of the adapter

        Returns:
            AdapterInfo for the adapter
        """
        adapter = self.get_adapter(name)
        return adapter.get_adapter_info()


# Global registry instance
global_adapter_registry = BenchmarkAdapterRegistry()
