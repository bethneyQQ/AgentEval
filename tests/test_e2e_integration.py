"""
End-to-end integration tests for the evaluation system.

Tests the complete flow from model adapter to benchmark evaluation to export.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from core.model_adapter_factory import ModelAdapterFactory
from core.batch_orchestrator import (
    BatchOrchestrator,
    EvaluationRequest,
    EvaluationConfig
)
from core.benchmark_registry import get_adapter
from core.export_handlers import HTMLExporter, CSVExporter, JSONExporter
from core.benchmark_adapter_base import (
    BaseTask,
    TaskResult,
    TaskStatus
)
from core.model_adapter_base import Message, GenerateResponse


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_complete_evaluation_flow_mock(self):
        """Test complete evaluation flow with mocked components."""
        # Setup
        output_dir = tempfile.mkdtemp()

        # Create evaluation request
        request = EvaluationRequest(
            model_name="gpt-4-turbo",
            benchmark_name="lm_eval",
            task_name="test_task",
            max_samples=3,
            output_dir=output_dir
        )

        # Create orchestrator
        orchestrator = BatchOrchestrator(max_concurrent=2)

        # Mock model factory
        with patch.object(orchestrator.model_factory, 'get_adapter') as mock_get_model:
            mock_model_adapter = AsyncMock()
            mock_model_adapter.generate.return_value = GenerateResponse(
                content="def test():\n    return True",
                finish_reason="stop",
                usage={"prompt_tokens": 10, "completion_tokens": 20},
                cost=0.001,
                latency=0.5
            )
            mock_model_info = Mock()
            mock_model_info.name = "gpt-4-turbo"
            mock_model_adapter.get_model_info = Mock(return_value=mock_model_info)
            mock_get_model.return_value = mock_model_adapter

            # Mock benchmark adapter
            with patch('core.batch_orchestrator.get_adapter') as mock_get_benchmark:
                mock_benchmark = MagicMock()
                mock_benchmark.__enter__.return_value = mock_benchmark
                mock_benchmark.__exit__.return_value = None

                mock_tasks = [
                    BaseTask(
                        task_id=f"task_{i}",
                        benchmark_name="lm_eval",
                        description=f"Test task {i}",
                        language="python",
                        metadata={"prompt": f"Write a test function {i}"}
                    )
                    for i in range(3)
                ]
                mock_benchmark.load_tasks.return_value = mock_tasks

                mock_benchmark.evaluate_task.return_value = TaskResult(
                    task_id="test",
                    benchmark_name="lm_eval",
                    status=TaskStatus.COMPLETED,
                    passed=True,
                    score=0.95,
                    execution_time=0.5
                )

                mock_get_benchmark.return_value = mock_benchmark

                # Run evaluation
                result = await orchestrator.run_evaluation(request)

                # Verify evaluation results
                assert result.error is None
                assert len(result.task_results) == 3
                assert all(r.passed for r in result.task_results)
                assert result.summary["total_tasks"] == 3
                assert result.summary["pass_rate"] == 1.0

                # Verify files were saved
                output_path = Path(output_dir)
                assert len(list(output_path.glob("*_summary.json"))) == 1
                assert len(list(output_path.glob("*_results.jsonl"))) == 1

    @pytest.mark.asyncio
    async def test_evaluation_with_export(self):
        """Test evaluation with multiple export formats."""
        output_dir = tempfile.mkdtemp()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark",
            max_samples=2,
            output_dir=output_dir
        )

        orchestrator = BatchOrchestrator(max_concurrent=1)

        # Mock components
        with patch.object(orchestrator.model_factory, 'get_adapter') as mock_get_model:
            mock_model_adapter = AsyncMock()
            mock_model_adapter.generate.return_value = GenerateResponse(
                content="test output",
                finish_reason="stop"
            )
            mock_model_info = Mock()
            mock_model_info.name = "test-model"
            mock_model_adapter.get_model_info = Mock(return_value=mock_model_info)
            mock_get_model.return_value = mock_model_adapter

            with patch('core.batch_orchestrator.get_adapter') as mock_get_benchmark:
                mock_benchmark = MagicMock()
                mock_benchmark.__enter__.return_value = mock_benchmark
                mock_benchmark.__exit__.return_value = None

                mock_tasks = [
                    BaseTask(
                        task_id=f"task_{i}",
                        benchmark_name="test-benchmark",
                        description=f"Task {i}",
                        language="python",
                        metadata={"prompt": f"Prompt {i}"}
                    )
                    for i in range(2)
                ]
                mock_benchmark.load_tasks.return_value = mock_tasks

                mock_benchmark.evaluate_task.return_value = TaskResult(
                    task_id="test",
                    benchmark_name="test-benchmark",
                    status=TaskStatus.COMPLETED,
                    passed=True,
                    score=0.9,
                    execution_time=0.3
                )

                mock_get_benchmark.return_value = mock_benchmark

                # Run evaluation
                result = await orchestrator.run_evaluation(request)

                # Export to all formats
                html_exporter = HTMLExporter()
                csv_exporter = CSVExporter()
                json_exporter = JSONExporter()

                output_path = Path(output_dir)
                html_exporter.export(result, str(output_path / "report.html"))
                csv_exporter.export(result, str(output_path / "results.csv"))
                json_exporter.export(result, str(output_path / "results.json"))

                # Verify all exports exist
                assert (output_path / "report.html").exists()
                assert (output_path / "results.csv").exists()
                assert (output_path / "results.json").exists()

                # Verify HTML content
                with open(output_path / "report.html", 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    assert "test-model" in html_content
                    assert "test-benchmark" in html_content
                    assert "Task Results" in html_content

    @pytest.mark.asyncio
    async def test_evaluation_with_failures(self):
        """Test evaluation handling task failures gracefully."""
        output_dir = tempfile.mkdtemp()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark",
            max_samples=5,
            output_dir=output_dir
        )

        orchestrator = BatchOrchestrator(max_concurrent=2)

        with patch.object(orchestrator.model_factory, 'get_adapter') as mock_get_model:
            mock_model_adapter = AsyncMock()
            mock_model_adapter.generate.return_value = GenerateResponse(
                content="test output",
                finish_reason="stop"
            )
            mock_model_info = Mock()
            mock_model_info.name = "test-model"
            mock_model_adapter.get_model_info = Mock(return_value=mock_model_info)
            mock_get_model.return_value = mock_model_adapter

            with patch('core.batch_orchestrator.get_adapter') as mock_get_benchmark:
                mock_benchmark = MagicMock()
                mock_benchmark.__enter__.return_value = mock_benchmark
                mock_benchmark.__exit__.return_value = None

                mock_tasks = [
                    BaseTask(
                        task_id=f"task_{i}",
                        benchmark_name="test-benchmark",
                        description=f"Task {i}",
                        language="python",
                        metadata={"prompt": f"Prompt {i}"}
                    )
                    for i in range(5)
                ]
                mock_benchmark.load_tasks.return_value = mock_tasks

                # Mix of passed and failed results
                def side_effect_evaluate(task, *args, **kwargs):
                    task_num = int(task.task_id.split('_')[1])
                    if task_num % 2 == 0:
                        return TaskResult(
                            task_id=task.task_id,
                            benchmark_name="test-benchmark",
                            status=TaskStatus.COMPLETED,
                            passed=True,
                            score=0.9,
                            execution_time=0.3
                        )
                    else:
                        return TaskResult(
                            task_id=task.task_id,
                            benchmark_name="test-benchmark",
                            status=TaskStatus.COMPLETED,
                            passed=False,
                            score=0.3,
                            execution_time=0.2
                        )

                mock_benchmark.evaluate_task.side_effect = side_effect_evaluate
                mock_get_benchmark.return_value = mock_benchmark

                # Run evaluation
                result = await orchestrator.run_evaluation(request)

                # Verify mixed results
                assert result.error is None
                assert len(result.task_results) == 5

                passed_count = sum(1 for r in result.task_results if r.passed)
                failed_count = sum(1 for r in result.task_results if not r.passed)

                assert passed_count == 3  # tasks 0, 2, 4
                assert failed_count == 2  # tasks 1, 3
                assert result.summary["pass_rate"] == 0.6

    @pytest.mark.asyncio
    async def test_concurrent_evaluation_correctness(self):
        """Test that concurrent evaluation produces correct results."""
        output_dir = tempfile.mkdtemp()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark",
            max_samples=10,
            output_dir=output_dir
        )

        # Test with different concurrency levels
        for max_concurrent in [1, 5, 10]:
            orchestrator = BatchOrchestrator(max_concurrent=max_concurrent)

            with patch.object(orchestrator.model_factory, 'get_adapter') as mock_get_model:
                mock_model_adapter = AsyncMock()
                mock_model_adapter.generate.return_value = GenerateResponse(
                    content="test output",
                    finish_reason="stop"
                )
                mock_model_info = Mock()
                mock_model_info.name = "test-model"
                mock_model_adapter.get_model_info = Mock(return_value=mock_model_info)
                mock_get_model.return_value = mock_model_adapter

                with patch('core.batch_orchestrator.get_adapter') as mock_get_benchmark:
                    mock_benchmark = MagicMock()
                    mock_benchmark.__enter__.return_value = mock_benchmark
                    mock_benchmark.__exit__.return_value = None

                    mock_tasks = [
                        BaseTask(
                            task_id=f"task_{i}",
                            benchmark_name="test-benchmark",
                            description=f"Task {i}",
                            language="python",
                            metadata={"prompt": f"Prompt {i}"}
                        )
                        for i in range(10)
                    ]
                    mock_benchmark.load_tasks.return_value = mock_tasks

                    mock_benchmark.evaluate_task.return_value = TaskResult(
                        task_id="test",
                        benchmark_name="test-benchmark",
                        status=TaskStatus.COMPLETED,
                        passed=True,
                        score=0.9,
                        execution_time=0.1
                    )

                    mock_get_benchmark.return_value = mock_benchmark

                    # Run evaluation
                    result = await orchestrator.run_evaluation(request)

                    # Verify results are consistent regardless of concurrency
                    assert result.error is None
                    assert len(result.task_results) == 10
                    assert result.summary["total_tasks"] == 10
                    assert result.summary["passed_tasks"] == 10

    @pytest.mark.asyncio
    async def test_metrics_calculation_integration(self):
        """Test that metrics are correctly calculated across the pipeline."""
        output_dir = tempfile.mkdtemp()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark",
            max_samples=5,
            output_dir=output_dir
        )

        orchestrator = BatchOrchestrator(max_concurrent=2)

        with patch.object(orchestrator.model_factory, 'get_adapter') as mock_get_model:
            mock_model_adapter = AsyncMock()
            mock_model_adapter.generate.return_value = GenerateResponse(
                content="test output",
                finish_reason="stop"
            )
            mock_model_info = Mock()
            mock_model_info.name = "test-model"
            mock_model_adapter.get_model_info = Mock(return_value=mock_model_info)
            mock_get_model.return_value = mock_model_adapter

            with patch('core.batch_orchestrator.get_adapter') as mock_get_benchmark:
                mock_benchmark = MagicMock()
                mock_benchmark.__enter__.return_value = mock_benchmark
                mock_benchmark.__exit__.return_value = None

                mock_tasks = [
                    BaseTask(
                        task_id=f"task_{i}",
                        benchmark_name="test-benchmark",
                        description=f"Task {i}",
                        language="python",
                        metadata={"prompt": f"Prompt {i}"}
                    )
                    for i in range(5)
                ]
                mock_benchmark.load_tasks.return_value = mock_tasks

                # Create results with specific scores
                def side_effect_evaluate(task, *args, **kwargs):
                    task_num = int(task.task_id.split('_')[1])
                    return TaskResult(
                        task_id=task.task_id,
                        benchmark_name="test-benchmark",
                        status=TaskStatus.COMPLETED,
                        passed=task_num < 3,  # First 3 pass
                        score=0.9 if task_num < 3 else 0.3,
                        execution_time=0.1 * (task_num + 1)
                    )

                mock_benchmark.evaluate_task.side_effect = side_effect_evaluate
                mock_get_benchmark.return_value = mock_benchmark

                # Run evaluation
                result = await orchestrator.run_evaluation(request)

                # Verify metrics
                assert result.error is None
                assert result.summary["total_tasks"] == 5
                assert result.summary["passed_tasks"] == 3
                assert result.summary["failed_tasks"] == 2
                assert result.summary["pass_rate"] == 0.6

                # Average score should be (0.9*3 + 0.3*2) / 5 = 0.66
                assert abs(result.summary["average_score"] - 0.66) < 0.01

                # Check that metrics were calculated
                assert len(result.metrics) > 0

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling throughout the pipeline."""
        output_dir = tempfile.mkdtemp()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark",
            max_samples=3,
            output_dir=output_dir
        )

        orchestrator = BatchOrchestrator(max_concurrent=2)

        with patch.object(orchestrator.model_factory, 'get_adapter') as mock_get_model:
            mock_model_adapter = AsyncMock()

            # Make generate fail for some tasks
            call_count = 0
            def side_effect_generate(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 2:
                    raise Exception("Model generation error")
                return GenerateResponse(
                    content="test output",
                    finish_reason="stop"
                )

            mock_model_adapter.generate.side_effect = side_effect_generate
            mock_model_info = Mock()
            mock_model_info.name = "test-model"
            mock_model_adapter.get_model_info = Mock(return_value=mock_model_info)
            mock_get_model.return_value = mock_model_adapter

            with patch('core.batch_orchestrator.get_adapter') as mock_get_benchmark:
                mock_benchmark = MagicMock()
                mock_benchmark.__enter__.return_value = mock_benchmark
                mock_benchmark.__exit__.return_value = None

                mock_tasks = [
                    BaseTask(
                        task_id=f"task_{i}",
                        benchmark_name="test-benchmark",
                        description=f"Task {i}",
                        language="python",
                        metadata={"prompt": f"Prompt {i}"}
                    )
                    for i in range(3)
                ]
                mock_benchmark.load_tasks.return_value = mock_tasks

                mock_benchmark.evaluate_task.return_value = TaskResult(
                    task_id="test",
                    benchmark_name="test-benchmark",
                    status=TaskStatus.COMPLETED,
                    passed=True,
                    score=0.9,
                    execution_time=0.1
                )

                mock_get_benchmark.return_value = mock_benchmark

                # Run evaluation
                result = await orchestrator.run_evaluation(request)

                # Verify that error was handled
                assert result.error is None
                assert len(result.task_results) == 3

                # One task should have error status
                error_count = sum(1 for r in result.task_results if r.status == TaskStatus.ERROR)
                assert error_count == 1

                # Summary should reflect the error
                assert result.summary["error_tasks"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
