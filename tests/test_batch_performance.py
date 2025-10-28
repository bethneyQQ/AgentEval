"""
Performance tests for the batch evaluation system.

Tests performance characteristics like throughput, latency, and scalability.
"""

import pytest
import asyncio
import time
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from core.batch_orchestrator import (
    BatchOrchestrator,
    EvaluationRequest,
    EvaluationConfig
)
from core.benchmark_adapter_base import (
    BaseTask,
    TaskResult,
    TaskStatus
)
from core.model_adapter_base import GenerateResponse


class TestBatchPerformance:
    """Performance tests for batch evaluation."""

    @pytest.mark.asyncio
    async def test_concurrent_execution_speedup(self):
        """Test that concurrent execution provides speedup."""
        output_dir = tempfile.mkdtemp()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark",
            max_samples=10,
            output_dir=output_dir
        )

        # Measure time with concurrency=1
        orchestrator_sequential = BatchOrchestrator(max_concurrent=1)
        start_time_seq = time.time()

        with patch.object(orchestrator_sequential.model_factory, 'get_adapter') as mock_get_model:
            mock_model_adapter = AsyncMock()

            async def slow_generate(*args, **kwargs):
                await asyncio.sleep(0.1)  # Simulate 100ms latency
                return GenerateResponse(
                    content="test output",
                    finish_reason="stop"
                )

            mock_model_adapter.generate.side_effect = slow_generate
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
                    execution_time=0.01
                )

                mock_get_benchmark.return_value = mock_benchmark

                result_seq = await orchestrator_sequential.run_evaluation(request)

        time_seq = time.time() - start_time_seq

        # Measure time with concurrency=5
        orchestrator_concurrent = BatchOrchestrator(max_concurrent=5)
        start_time_conc = time.time()

        with patch.object(orchestrator_concurrent.model_factory, 'get_adapter') as mock_get_model:
            mock_model_adapter = AsyncMock()
            mock_model_adapter.generate.side_effect = slow_generate
            mock_model_info = Mock()
            mock_model_info.name = "test-model"
            mock_model_adapter.get_model_info = Mock(return_value=mock_model_info)
            mock_get_model.return_value = mock_model_adapter

            with patch('core.batch_orchestrator.get_adapter') as mock_get_benchmark:
                mock_benchmark = MagicMock()
                mock_benchmark.__enter__.return_value = mock_benchmark
                mock_benchmark.__exit__.return_value = None
                mock_benchmark.load_tasks.return_value = mock_tasks
                mock_benchmark.evaluate_task.return_value = TaskResult(
                    task_id="test",
                    benchmark_name="test-benchmark",
                    status=TaskStatus.COMPLETED,
                    passed=True,
                    score=0.9,
                    execution_time=0.01
                )

                mock_get_benchmark.return_value = mock_benchmark

                result_conc = await orchestrator_concurrent.run_evaluation(request)

        time_conc = time.time() - start_time_conc

        # Verify speedup
        speedup = time_seq / time_conc
        print(f"\nSequential time: {time_seq:.2f}s")
        print(f"Concurrent time: {time_conc:.2f}s")
        print(f"Speedup: {speedup:.2f}x")

        assert speedup > 2.0, f"Expected speedup > 2x, got {speedup:.2f}x"

        # Verify results are the same
        assert result_seq.summary["total_tasks"] == result_conc.summary["total_tasks"]
        assert result_seq.summary["pass_rate"] == result_conc.summary["pass_rate"]

    @pytest.mark.asyncio
    async def test_large_batch_performance(self):
        """Test performance with large batch of tasks."""
        output_dir = tempfile.mkdtemp()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark",
            max_samples=100,
            output_dir=output_dir
        )

        orchestrator = BatchOrchestrator(max_concurrent=10)

        start_time = time.time()

        with patch.object(orchestrator.model_factory, 'get_adapter') as mock_get_model:
            mock_model_adapter = AsyncMock()

            async def fast_generate(*args, **kwargs):
                await asyncio.sleep(0.01)  # 10ms latency
                return GenerateResponse(
                    content="test output",
                    finish_reason="stop"
                )

            mock_model_adapter.generate.side_effect = fast_generate
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
                    for i in range(100)
                ]
                mock_benchmark.load_tasks.return_value = mock_tasks

                mock_benchmark.evaluate_task.return_value = TaskResult(
                    task_id="test",
                    benchmark_name="test-benchmark",
                    status=TaskStatus.COMPLETED,
                    passed=True,
                    score=0.9,
                    execution_time=0.01
                )

                mock_get_benchmark.return_value = mock_benchmark

                result = await orchestrator.run_evaluation(request)

        elapsed_time = time.time() - start_time

        print(f"\nLarge batch (100 tasks) time: {elapsed_time:.2f}s")

        assert elapsed_time < 2.0, f"Large batch took too long: {elapsed_time:.2f}s"
        assert result.summary["total_tasks"] == 100

        # Calculate throughput
        throughput = 100 / elapsed_time
        print(f"Throughput: {throughput:.1f} tasks/second")

    @pytest.mark.asyncio
    async def test_export_performance(self):
        """Test export performance with large results."""
        from core.export_handlers import HTMLExporter, CSVExporter, JSONExporter
        from datetime import datetime

        output_dir = tempfile.mkdtemp()

        # Create a large result
        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark",
            max_samples=100
        )

        task_results = [
            TaskResult(
                task_id=f"task_{i}",
                benchmark_name="test-benchmark",
                status=TaskStatus.COMPLETED,
                passed=i % 2 == 0,
                score=0.9 if i % 2 == 0 else 0.3,
                execution_time=0.1 * i
            )
            for i in range(100)
        ]

        from core.batch_orchestrator import EvaluationResult

        result = EvaluationResult(
            request=request,
            task_results=task_results,
            metrics={},
            summary={
                "total_tasks": 100,
                "passed_tasks": 50,
                "failed_tasks": 50,
                "pass_rate": 0.5
            },
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_time=10.0
        )

        # Test HTML export performance
        html_exporter = HTMLExporter()
        start_time = time.time()
        html_exporter.export(result, str(Path(output_dir) / "report.html"))
        html_time = time.time() - start_time
        print(f"\nHTML export time (100 tasks): {html_time:.3f}s")
        assert html_time < 1.0

        # Test CSV export performance
        csv_exporter = CSVExporter()
        start_time = time.time()
        csv_exporter.export(result, str(Path(output_dir) / "results.csv"))
        csv_time = time.time() - start_time
        print(f"CSV export time (100 tasks): {csv_time:.3f}s")
        assert csv_time < 0.5

        # Test JSON export performance
        json_exporter = JSONExporter()
        start_time = time.time()
        json_exporter.export(result, str(Path(output_dir) / "results.json"))
        json_time = time.time() - start_time
        print(f"JSON export time (100 tasks): {json_time:.3f}s")
        assert json_time < 0.5

    @pytest.mark.asyncio
    async def test_scalability_different_concurrency_levels(self):
        """Test scalability with different concurrency levels."""
        output_dir = tempfile.mkdtemp()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark",
            max_samples=20,
            output_dir=output_dir
        )

        results_timing = {}

        for concurrency in [1, 2, 5, 10, 20]:
            orchestrator = BatchOrchestrator(max_concurrent=concurrency)

            start_time = time.time()

            with patch.object(orchestrator.model_factory, 'get_adapter') as mock_get_model:
                mock_model_adapter = AsyncMock()

                async def generate_with_delay(*args, **kwargs):
                    await asyncio.sleep(0.05)  # 50ms delay
                    return GenerateResponse(
                        content="test output",
                        finish_reason="stop"
                    )

                mock_model_adapter.generate.side_effect = generate_with_delay
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
                        for i in range(20)
                    ]
                    mock_benchmark.load_tasks.return_value = mock_tasks

                    mock_benchmark.evaluate_task.return_value = TaskResult(
                        task_id="test",
                        benchmark_name="test-benchmark",
                        status=TaskStatus.COMPLETED,
                        passed=True,
                        score=0.9,
                        execution_time=0.01
                    )

                    mock_get_benchmark.return_value = mock_benchmark

                    result = await orchestrator.run_evaluation(request)

            elapsed_time = time.time() - start_time
            results_timing[concurrency] = elapsed_time

            print(f"\nConcurrency {concurrency}: {elapsed_time:.2f}s")

        # Verify that increasing concurrency improves performance
        assert results_timing[1] > results_timing[5], "Higher concurrency should be faster"
        assert results_timing[5] > results_timing[10], "Even higher concurrency should be faster still"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
