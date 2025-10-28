"""
Tests for Enhanced Metrics Engine.
"""

import pytest
from dataclasses import dataclass
from core.enhanced_metrics import (
    EnhancedMetricsEngine, MetricDefinition, MetricResult
)


@dataclass
class MockResult:
    """Mock result for testing."""
    passed: bool
    execution_time: float
    score: float = 0.0


class TestEnhancedMetricsEngine:
    """Tests for EnhancedMetricsEngine."""

    def test_engine_initialization(self):
        """Test engine initializes with built-in metrics."""
        engine = EnhancedMetricsEngine()
        metrics = engine.list_metrics()

        assert "total_tasks" in metrics
        assert "pass_rate" in metrics
        assert "avg_execution_time" in metrics

    def test_register_custom_metric(self):
        """Test registering a custom metric."""
        engine = EnhancedMetricsEngine()

        def custom_metric(results):
            return len(results) * 2.0

        engine.register_metric(
            "double_count",
            custom_metric,
            category="custom",
            description="Double the count"
        )

        assert "double_count" in engine.list_metrics()

    def test_metric_decorator(self):
        """Test metric registration via decorator."""
        engine = EnhancedMetricsEngine()

        @engine.metric("triple_count", category="custom")
        def triple_count(results):
            return len(results) * 3.0

        assert "triple_count" in engine.list_metrics()

    def test_calculate_builtin_metrics(self):
        """Test calculating built-in metrics."""
        engine = EnhancedMetricsEngine()

        results = [
            MockResult(passed=True, execution_time=1.0),
            MockResult(passed=False, execution_time=2.0),
            MockResult(passed=True, execution_time=1.5),
        ]

        total = engine.calculate_metric("total_tasks", results)
        assert total.value == 3.0

        pass_rate = engine.calculate_metric("pass_rate", results)
        assert abs(pass_rate.value - 66.67) < 0.1

        avg_time = engine.calculate_metric("avg_execution_time", results)
        assert abs(avg_time.value - 1.5) < 0.01

    def test_calculate_custom_metric(self):
        """Test calculating custom metric."""
        engine = EnhancedMetricsEngine()

        @engine.metric("max_score", category="quality")
        def max_score(results):
            return max(r.score for r in results) if results else 0.0

        results = [
            MockResult(passed=True, execution_time=1.0, score=0.8),
            MockResult(passed=False, execution_time=2.0, score=0.5),
            MockResult(passed=True, execution_time=1.5, score=0.9),
        ]

        result = engine.calculate_metric("max_score", results)
        assert result.value == 0.9

    def test_calculate_all_metrics(self):
        """Test calculating all metrics."""
        engine = EnhancedMetricsEngine()

        results = [
            MockResult(passed=True, execution_time=1.0),
            MockResult(passed=False, execution_time=2.0),
        ]

        all_metrics = engine.calculate_all_metrics(results)

        assert "basic" in all_metrics
        assert "operational" in all_metrics

        basic_metrics = all_metrics["basic"]
        assert len(basic_metrics) > 0

    def test_calculate_metrics_by_category(self):
        """Test calculating metrics by category."""
        engine = EnhancedMetricsEngine()

        results = [MockResult(passed=True, execution_time=1.0)]

        metrics = engine.calculate_all_metrics(results, categories=["basic"])

        assert "basic" in metrics
        assert "operational" not in metrics

    def test_list_metrics_by_category(self):
        """Test listing metrics by category."""
        engine = EnhancedMetricsEngine()

        basic_metrics = engine.list_metrics(category="basic")
        assert "total_tasks" in basic_metrics
        assert "pass_rate" in basic_metrics

        operational_metrics = engine.list_metrics(category="operational")
        assert "avg_execution_time" in operational_metrics

    def test_calculate_unknown_metric_raises_error(self):
        """Test calculating unknown metric raises ValueError."""
        engine = EnhancedMetricsEngine()
        results = [MockResult(passed=True, execution_time=1.0)]

        with pytest.raises(ValueError, match="not registered"):
            engine.calculate_metric("unknown_metric", results)

    def test_empty_results(self):
        """Test metrics calculation with empty results."""
        engine = EnhancedMetricsEngine()
        results = []

        metrics = engine.calculate_all_metrics(results)
        assert isinstance(metrics, dict)

    def test_metric_overwriting_warning(self, caplog):
        """Test that overwriting a metric logs a warning."""
        engine = EnhancedMetricsEngine()

        def metric1(results):
            return 1.0

        def metric2(results):
            return 2.0

        engine.register_metric("test_metric", metric1)
        engine.register_metric("test_metric", metric2)

        assert "already registered" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
