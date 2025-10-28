"""
Enhanced Metrics Engine with extensibility support.

This module provides an extensible metrics calculation framework that allows
easy definition and registration of custom metrics.
"""

from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricDefinition:
    """Definition of a metric.

    Attributes:
        name: Unique name of the metric
        category: Category (basic, quality, operational, security, custom)
        calculator: Function that calculates the metric
        description: Human-readable description
        unit: Unit of measurement (empty string if unitless)
    """
    name: str
    category: str
    calculator: Callable
    description: str
    unit: str = ""


@dataclass
class MetricResult:
    """Result of a metric calculation."""
    name: str
    value: float
    category: str
    unit: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseMetricCalculator(ABC):
    """Base class for metric calculators."""

    @abstractmethod
    def calculate(self, results: List[Any]) -> float:
        """Calculate metric value from results."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Get additional metadata about the calculation."""
        pass


class EnhancedMetricsEngine:
    """
    Enhanced metrics engine with extensibility support.

    This engine allows registration of custom metrics through decorators
    or direct registration, making it easy to extend the evaluation system
    with domain-specific metrics.
    """

    def __init__(self):
        """Initialize the enhanced metrics engine."""
        self._metrics: Dict[str, MetricDefinition] = {}
        self._register_builtin_metrics()

    def register_metric(
        self,
        name: str,
        calculator: Callable,
        category: str = "custom",
        description: str = "",
        unit: str = ""
    ):
        """
        Register a custom metric.

        Args:
            name: Unique metric name
            calculator: Function that takes List[results] and returns float
            category: Metric category
            description: Human-readable description
            unit: Unit of measurement

        Example:
            def my_metric(results):
                return sum(r.score for r in results) / len(results)

            engine.register_metric("average_score", my_metric, "quality")
        """
        if name in self._metrics:
            logger.warning(f"Metric {name} already registered, overwriting")

        self._metrics[name] = MetricDefinition(
            name=name,
            category=category,
            calculator=calculator,
            description=description,
            unit=unit
        )
        logger.info(f"Registered metric: {name}")

    def metric(
        self,
        name: str,
        category: str = "custom",
        description: str = "",
        unit: str = ""
    ):
        """
        Decorator for registering metrics.

        Example:
            @engine.metric("pass_rate", category="basic", unit="%")
            def calculate_pass_rate(results):
                if not results:
                    return 0.0
                passed = sum(1 for r in results if r.passed)
                return (passed / len(results)) * 100.0
        """
        def decorator(func: Callable) -> Callable:
            self.register_metric(name, func, category, description, unit)
            return func
        return decorator

    def calculate_metric(
        self,
        name: str,
        results: List[Any]
    ) -> Optional[MetricResult]:
        """
        Calculate a specific metric.

        Args:
            name: Name of the metric to calculate
            results: List of evaluation results

        Returns:
            MetricResult or None if metric not found

        Raises:
            ValueError: If metric not registered
        """
        if name not in self._metrics:
            raise ValueError(f"Metric {name} not registered")

        metric_def = self._metrics[name]

        try:
            value = metric_def.calculator(results)
            return MetricResult(
                name=metric_def.name,
                value=value,
                category=metric_def.category,
                unit=metric_def.unit
            )
        except Exception as e:
            logger.error(f"Error calculating metric {name}: {str(e)}")
            return None

    def calculate_all_metrics(
        self,
        results: List[Any],
        categories: Optional[List[str]] = None
    ) -> Dict[str, List[MetricResult]]:
        """
        Calculate all registered metrics or metrics in specific categories.

        Args:
            results: List of evaluation results
            categories: List of categories to calculate (None = all)

        Returns:
            Dictionary mapping category to list of MetricResult
        """
        if not results:
            logger.warning("No results provided for metrics calculation")
            return {}

        metrics_by_category: Dict[str, List[MetricResult]] = {}

        for metric_name, metric_def in self._metrics.items():
            if categories is not None and metric_def.category not in categories:
                continue

            result = self.calculate_metric(metric_name, results)
            if result:
                if result.category not in metrics_by_category:
                    metrics_by_category[result.category] = []
                metrics_by_category[result.category].append(result)

        return metrics_by_category

    def list_metrics(self, category: Optional[str] = None) -> List[str]:
        """
        List all registered metrics, optionally filtered by category.

        Args:
            category: Category to filter by (None = all)

        Returns:
            List of metric names
        """
        if category is None:
            return list(self._metrics.keys())
        return [
            name for name, metric in self._metrics.items()
            if metric.category == category
        ]

    def _register_builtin_metrics(self):
        """Register built-in metrics."""

        @self.metric("total_tasks", category="basic", description="Total number of tasks", unit="count")
        def total_tasks(results):
            return len(results)

        @self.metric("pass_rate", category="basic", description="Percentage of passed tasks", unit="%")
        def pass_rate(results):
            if not results:
                return 0.0
            passed = sum(1 for r in results if getattr(r, 'passed', False))
            return (passed / len(results)) * 100.0

        @self.metric("avg_execution_time", category="operational", description="Average execution time", unit="s")
        def avg_execution_time(results):
            times = [r.execution_time for r in results if hasattr(r, 'execution_time') and r.execution_time is not None]
            return sum(times) / len(times) if times else 0.0


# Global instance for convenience
global_metrics_engine = EnhancedMetricsEngine()
