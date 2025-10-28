"""
Tests for export handlers.
"""

import pytest
import json
import csv
from pathlib import Path
import tempfile
from datetime import datetime

from core.export_handlers import HTMLExporter, CSVExporter, JSONExporter
from core.batch_orchestrator import EvaluationRequest, EvaluationResult
from core.benchmark_adapter_base import TaskResult, TaskStatus
from core.enhanced_metrics import MetricResult


class TestHTMLExporter:
    """Tests for HTMLExporter."""

    def test_html_exporter_initialization(self):
        """Test HTML exporter initialization."""
        exporter = HTMLExporter()
        assert exporter.template_path is None

        exporter_with_template = HTMLExporter(template_path="/path/to/template.html")
        assert exporter_with_template.template_path == "/path/to/template.html"

    def test_export_html_creates_file(self):
        """Test that HTML export creates a file."""
        exporter = HTMLExporter()

        request = EvaluationRequest(
            model_name="gpt-4-turbo",
            benchmark_name="test-benchmark"
        )

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="test-benchmark",
                status=TaskStatus.COMPLETED,
                passed=True,
                score=0.95,
                execution_time=1.5
            )
        ]

        result = EvaluationResult(
            request=request,
            task_results=task_results,
            metrics={},
            summary={"total_tasks": 1, "passed_tasks": 1, "pass_rate": 1.0},
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_time=2.0
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            exporter.export(result, str(output_path))

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_export_html_content_structure(self):
        """Test that HTML export contains expected structure."""
        exporter = HTMLExporter()

        request = EvaluationRequest(
            model_name="gpt-4-turbo",
            benchmark_name="test-benchmark",
            task_name="test-task"
        )

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="test-benchmark",
                status=TaskStatus.COMPLETED,
                passed=True,
                score=0.95,
                execution_time=1.5
            )
        ]

        result = EvaluationResult(
            request=request,
            task_results=task_results,
            metrics={},
            summary={
                "total_tasks": 1,
                "passed_tasks": 1,
                "failed_tasks": 0,
                "error_tasks": 0,
                "pass_rate": 1.0,
                "average_score": 0.95,
                "average_execution_time": 1.5
            },
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_time=2.0
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            exporter.export(result, str(output_path))

            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check basic HTML structure
            assert "<!DOCTYPE html>" in content
            assert "<html" in content
            assert "<head>" in content
            assert "<body>" in content
            assert "</html>" in content

            # Check title
            assert "gpt-4-turbo" in content
            assert "test-benchmark" in content

            # Check summary section
            assert "Summary" in content
            assert "Total Tasks" in content
            assert "Passed Tasks" in content
            assert "Pass Rate" in content

            # Check task results section
            assert "Task Results" in content
            assert "task_1" in content

    def test_export_html_with_metrics(self):
        """Test HTML export with metrics."""
        exporter = HTMLExporter()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark"
        )

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="test-benchmark",
                status=TaskStatus.COMPLETED,
                passed=True,
                score=0.9,
                execution_time=1.0
            )
        ]

        metrics = {
            "performance": [
                MetricResult(
                    name="accuracy",
                    value=0.95,
                    category="performance",
                    unit="ratio"
                ),
                MetricResult(
                    name="f1_score",
                    value=0.93,
                    category="performance",
                    unit="ratio"
                )
            ]
        }

        result = EvaluationResult(
            request=request,
            task_results=task_results,
            metrics=metrics,
            summary={"total_tasks": 1, "passed_tasks": 1, "pass_rate": 1.0},
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_time=1.5
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            exporter.export(result, str(output_path))

            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "Metrics" in content
            assert "accuracy" in content
            assert "f1_score" in content
            assert "0.95" in content
            assert "0.93" in content

    def test_export_html_with_errors(self):
        """Test HTML export with error tasks."""
        exporter = HTMLExporter()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark"
        )

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="test-benchmark",
                status=TaskStatus.ERROR,
                passed=False,
                score=0.0,
                execution_time=0.0,
                error_message="Test error message"
            )
        ]

        result = EvaluationResult(
            request=request,
            task_results=task_results,
            metrics={},
            summary={
                "total_tasks": 1,
                "passed_tasks": 0,
                "failed_tasks": 0,
                "error_tasks": 1,
                "pass_rate": 0.0
            },
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_time=1.0
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            exporter.export(result, str(output_path))

            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "Test error message" in content
            assert "error" in content


class TestCSVExporter:
    """Tests for CSVExporter."""

    def test_csv_exporter_initialization(self):
        """Test CSV exporter initialization."""
        exporter = CSVExporter()
        assert exporter is not None

    def test_export_csv_creates_file(self):
        """Test that CSV export creates a file."""
        exporter = CSVExporter()

        request = EvaluationRequest(
            model_name="gpt-4-turbo",
            benchmark_name="test-benchmark"
        )

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="test-benchmark",
                status=TaskStatus.COMPLETED,
                passed=True,
                score=0.95,
                execution_time=1.5
            )
        ]

        result = EvaluationResult(
            request=request,
            task_results=task_results,
            metrics={},
            summary={"total_tasks": 1, "passed_tasks": 1, "pass_rate": 1.0},
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_time=2.0
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.csv"
            exporter.export(result, str(output_path))

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_export_csv_content_structure(self):
        """Test that CSV export contains expected structure."""
        exporter = CSVExporter()

        request = EvaluationRequest(
            model_name="gpt-4-turbo",
            benchmark_name="test-benchmark"
        )

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="test-benchmark",
                status=TaskStatus.COMPLETED,
                passed=True,
                score=0.95,
                execution_time=1.5
            ),
            TaskResult(
                task_id="task_2",
                benchmark_name="test-benchmark",
                status=TaskStatus.COMPLETED,
                passed=False,
                score=0.45,
                execution_time=1.2
            )
        ]

        result = EvaluationResult(
            request=request,
            task_results=task_results,
            metrics={},
            summary={
                "total_tasks": 2,
                "passed_tasks": 1,
                "failed_tasks": 1,
                "pass_rate": 0.5
            },
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_time=3.0
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.csv"
            exporter.export(result, str(output_path))

            with open(output_path, 'r', newline='', encoding='utf-8') as f:
                content = f.read()

            # Check for summary section
            assert "EVALUATION SUMMARY" in content
            assert "gpt-4-turbo" in content
            assert "test-benchmark" in content

            # Check for task results section
            assert "TASK RESULTS" in content
            assert "task_1" in content
            assert "task_2" in content

    def test_export_csv_without_summary(self):
        """Test CSV export without summary section."""
        exporter = CSVExporter()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark"
        )

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="test-benchmark",
                status=TaskStatus.COMPLETED,
                passed=True,
                score=0.9,
                execution_time=1.0
            )
        ]

        result = EvaluationResult(
            request=request,
            task_results=task_results,
            metrics={},
            summary={"total_tasks": 1},
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_time=1.5
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.csv"
            exporter.export(result, str(output_path), include_summary=False)

            with open(output_path, 'r', newline='', encoding='utf-8') as f:
                content = f.read()

            # Should not have summary section
            assert "EVALUATION SUMMARY" not in content

            # But should have task results
            assert "TASK RESULTS" in content
            assert "task_1" in content

    def test_export_csv_readable_format(self):
        """Test that CSV is properly formatted and readable."""
        exporter = CSVExporter()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark"
        )

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="test-benchmark",
                status=TaskStatus.COMPLETED,
                passed=True,
                score=0.95,
                execution_time=1.5
            )
        ]

        result = EvaluationResult(
            request=request,
            task_results=task_results,
            metrics={},
            summary={"total_tasks": 1, "pass_rate": 1.0},
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_time=2.0
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.csv"
            exporter.export(result, str(output_path))

            # Read with csv.reader to verify format
            with open(output_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)

            # Should have multiple rows
            assert len(rows) > 5

            # Check that task results have correct number of columns
            task_results_start = None
            for i, row in enumerate(rows):
                if row and row[0] == "TASK RESULTS":
                    task_results_start = i
                    break

            assert task_results_start is not None

            # Header row should be after "TASK RESULTS"
            header_row = rows[task_results_start + 1]
            assert "Task ID" in header_row
            assert "Status" in header_row
            assert "Score" in header_row


class TestJSONExporter:
    """Tests for JSONExporter."""

    def test_json_exporter_initialization(self):
        """Test JSON exporter initialization."""
        exporter = JSONExporter()
        assert exporter is not None

    def test_export_json_creates_file(self):
        """Test that JSON export creates a file."""
        exporter = JSONExporter()

        request = EvaluationRequest(
            model_name="gpt-4-turbo",
            benchmark_name="test-benchmark"
        )

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="test-benchmark",
                status=TaskStatus.COMPLETED,
                passed=True,
                score=0.95,
                execution_time=1.5
            )
        ]

        result = EvaluationResult(
            request=request,
            task_results=task_results,
            metrics={},
            summary={"total_tasks": 1, "passed_tasks": 1, "pass_rate": 1.0},
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_time=2.0
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.json"
            exporter.export(result, str(output_path))

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_export_json_valid_structure(self):
        """Test that JSON export produces valid JSON with correct structure."""
        exporter = JSONExporter()

        request = EvaluationRequest(
            model_name="gpt-4-turbo",
            benchmark_name="test-benchmark",
            task_name="test-task"
        )

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="test-benchmark",
                status=TaskStatus.COMPLETED,
                passed=True,
                score=0.95,
                execution_time=1.5
            )
        ]

        result = EvaluationResult(
            request=request,
            task_results=task_results,
            metrics={},
            summary={"total_tasks": 1, "passed_tasks": 1, "pass_rate": 1.0},
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_time=2.0
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.json"
            exporter.export(result, str(output_path))

            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check structure
            assert "request" in data
            assert "summary" in data
            assert "metrics" in data
            assert "task_results" in data
            assert "timing" in data

            # Check request data
            assert data["request"]["model_name"] == "gpt-4-turbo"
            assert data["request"]["benchmark_name"] == "test-benchmark"
            assert data["request"]["task_name"] == "test-task"

            # Check task results
            assert len(data["task_results"]) == 1
            assert data["task_results"][0]["task_id"] == "task_1"
            assert data["task_results"][0]["passed"] is True

    def test_export_json_with_metrics(self):
        """Test JSON export with metrics."""
        exporter = JSONExporter()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark"
        )

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="test-benchmark",
                status=TaskStatus.COMPLETED,
                passed=True,
                score=0.9,
                execution_time=1.0
            )
        ]

        metrics = {
            "performance": [
                MetricResult(
                    name="accuracy",
                    value=0.95,
                    category="performance",
                    unit="ratio"
                )
            ]
        }

        result = EvaluationResult(
            request=request,
            task_results=task_results,
            metrics=metrics,
            summary={"total_tasks": 1},
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_time=1.5
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.json"
            exporter.export(result, str(output_path))

            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert "performance" in data["metrics"]
            assert len(data["metrics"]["performance"]) == 1
            assert data["metrics"]["performance"][0]["name"] == "accuracy"
            assert data["metrics"]["performance"][0]["value"] == 0.95

    def test_export_json_custom_indent(self):
        """Test JSON export with custom indentation."""
        exporter = JSONExporter()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark"
        )

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="test-benchmark",
                status=TaskStatus.COMPLETED,
                passed=True,
                score=0.9,
                execution_time=1.0
            )
        ]

        result = EvaluationResult(
            request=request,
            task_results=task_results,
            metrics={},
            summary={"total_tasks": 1},
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_time=1.5
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # Export with no indentation
            output_path_compact = Path(tmpdir) / "compact.json"
            exporter.export(result, str(output_path_compact), indent=0)

            # Export with 4-space indentation
            output_path_pretty = Path(tmpdir) / "pretty.json"
            exporter.export(result, str(output_path_pretty), indent=4)

            # Compact should be smaller
            compact_size = output_path_compact.stat().st_size
            pretty_size = output_path_pretty.stat().st_size

            assert pretty_size > compact_size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
