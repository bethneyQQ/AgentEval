"""
Tests for Batch Orchestrator.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import tempfile
import json

from core.batch_orchestrator import (
    BatchOrchestrator,
    EvaluationRequest,
    EvaluationResult,
    EvaluationConfig
)
from core.benchmark_adapter_base import (
    BaseTask,
    TaskResult,
    TaskStatus
)
from core.model_adapter_base import Message, GenerateResponse


class TestEvaluationRequest:
    """Tests for EvaluationRequest."""

    def test_evaluation_request_creation(self):
        """Test creating evaluation request."""
        request = EvaluationRequest(
            model_name="gpt-4-turbo",
            benchmark_name="lm_eval",
            task_name="single_turn_scenarios_function_generation",
            max_samples=10
        )

        assert request.model_name == "gpt-4-turbo"
        assert request.benchmark_name == "lm_eval"
        assert request.task_name == "single_turn_scenarios_function_generation"
        assert request.max_samples == 10

    def test_evaluation_request_with_metadata(self):
        """Test evaluation request with metadata."""
        request = EvaluationRequest(
            model_name="gpt-4-turbo",
            benchmark_name="lm_eval",
            metadata={"experiment_id": "exp_001", "author": "test"}
        )

        assert request.metadata["experiment_id"] == "exp_001"
        assert request.metadata["author"] == "test"


class TestEvaluationResult:
    """Tests for EvaluationResult."""

    def test_evaluation_result_creation(self):
        """Test creating evaluation result."""
        request = EvaluationRequest(
            model_name="gpt-4-turbo",
            benchmark_name="lm_eval"
        )

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="lm_eval",
                status=TaskStatus.COMPLETED,
                passed=True,
                score=0.9,
                execution_time=1.5
            )
        ]

        result = EvaluationResult(
            request=request,
            task_results=task_results,
            metrics={},
            summary={"pass_rate": 1.0},
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_time=5.0
        )

        assert result.request == request
        assert len(result.task_results) == 1
        assert result.summary["pass_rate"] == 1.0
        assert result.total_time == 5.0
        assert result.error is None


class TestBatchOrchestrator:
    """Tests for BatchOrchestrator."""

    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = BatchOrchestrator(
            max_concurrent=10,
            enable_progress=True
        )

        assert orchestrator.max_concurrent == 10
        assert orchestrator.enable_progress is True
        assert orchestrator.metrics_engine is not None

    def test_orchestrator_default_values(self):
        """Test orchestrator default values."""
        orchestrator = BatchOrchestrator()

        assert orchestrator.max_concurrent == 5
        assert orchestrator.enable_progress is True

    def test_generate_summary(self):
        """Test summary generation."""
        orchestrator = BatchOrchestrator()

        task_results = [
            TaskResult(
                task_id=f"task_{i}",
                benchmark_name="test",
                status=TaskStatus.COMPLETED,
                passed=i % 2 == 0,
                score=0.8 if i % 2 == 0 else 0.3,
                execution_time=1.0 + i * 0.1
            )
            for i in range(10)
        ]

        summary = orchestrator._generate_summary(task_results, {})

        assert summary["total_tasks"] == 10
        assert summary["passed_tasks"] == 5
        assert summary["failed_tasks"] == 5
        assert summary["error_tasks"] == 0
        assert summary["pass_rate"] == 0.5
        assert 0.0 < summary["average_score"] < 1.0
        assert summary["average_execution_time"] > 0

    def test_generate_summary_with_errors(self):
        """Test summary generation with error tasks."""
        orchestrator = BatchOrchestrator()

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="test",
                status=TaskStatus.COMPLETED,
                passed=True,
                score=0.9,
                execution_time=1.0
            ),
            TaskResult(
                task_id="task_2",
                benchmark_name="test",
                status=TaskStatus.ERROR,
                passed=False,
                score=0.0,
                execution_time=0.0,
                error_message="Test error"
            )
        ]

        summary = orchestrator._generate_summary(task_results, {})

        assert summary["total_tasks"] == 2
        assert summary["passed_tasks"] == 1
        assert summary["error_tasks"] == 1

    @pytest.mark.asyncio
    async def test_execute_single_task(self):
        """Test executing a single task."""
        orchestrator = BatchOrchestrator()

        # Mock task
        task = BaseTask(
            task_id="test_001",
            benchmark_name="test",
            description="Test task",
            language="python",
            metadata={"prompt": "Write a hello function"}
        )

        # Mock model adapter
        mock_model_adapter = AsyncMock()
        mock_model_adapter.generate.return_value = GenerateResponse(
            content="def hello():\n    print('Hello')",
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            cost=0.01,
            latency=0.5
        )
        mock_model_info = Mock()
        mock_model_info.name = "test-model"
        # get_model_info should not be async
        mock_model_adapter.get_model_info = Mock(return_value=mock_model_info)

        # Mock benchmark adapter
        mock_benchmark_adapter = Mock()
        mock_benchmark_adapter.evaluate_task.return_value = TaskResult(
            task_id="test_001",
            benchmark_name="test",
            status=TaskStatus.COMPLETED,
            passed=True,
            score=0.95,
            execution_time=0.5
        )

        config = EvaluationConfig()

        result = await orchestrator._execute_single_task(
            task,
            mock_model_adapter,
            mock_benchmark_adapter,
            config
        )

        assert result.task_id == "test_001"
        assert result.passed is True
        assert result.score == 0.95

        # Verify model adapter was called
        mock_model_adapter.generate.assert_called_once()

        # Verify benchmark adapter was called
        mock_benchmark_adapter.evaluate_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_single_task_error_handling(self):
        """Test error handling in single task execution."""
        orchestrator = BatchOrchestrator()

        task = BaseTask(
            task_id="test_001",
            benchmark_name="test",
            description="Test task",
            language="python"
        )

        # Mock model adapter that raises error
        mock_model_adapter = AsyncMock()
        mock_model_adapter.generate.side_effect = Exception("Model error")

        mock_benchmark_adapter = Mock()
        config = EvaluationConfig()

        result = await orchestrator._execute_single_task(
            task,
            mock_model_adapter,
            mock_benchmark_adapter,
            config
        )

        # Should return error result
        assert result.status == TaskStatus.ERROR
        assert result.passed is False
        assert result.error_message == "Model error"

    @pytest.mark.asyncio
    async def test_execute_tasks_concurrent(self):
        """Test concurrent task execution."""
        orchestrator = BatchOrchestrator(max_concurrent=3)

        tasks = [
            BaseTask(
                task_id=f"task_{i}",
                benchmark_name="test",
                description=f"Task {i}",
                language="python",
                metadata={"prompt": f"Task {i}"}
            )
            for i in range(5)
        ]

        # Mock model and benchmark adapters
        mock_model_adapter = AsyncMock()
        mock_model_adapter.generate.return_value = GenerateResponse(
            content="test",
            finish_reason="stop"
        )
        mock_model_info = Mock()
        mock_model_info.name = "test-model"
        # get_model_info should not be async
        mock_model_adapter.get_model_info = Mock(return_value=mock_model_info)

        mock_benchmark_adapter = Mock()
        mock_benchmark_adapter.evaluate_task.return_value = TaskResult(
            task_id="test",
            benchmark_name="test",
            status=TaskStatus.COMPLETED,
            passed=True,
            score=0.8,
            execution_time=0.1
        )

        config = EvaluationConfig()

        results = await orchestrator._execute_tasks_concurrent(
            tasks,
            mock_model_adapter,
            mock_benchmark_adapter,
            config
        )

        assert len(results) == 5
        assert all(isinstance(r, TaskResult) for r in results)

        # Verify model adapter was called for each task
        assert mock_model_adapter.generate.call_count == 5

    @pytest.mark.asyncio
    async def test_execute_tasks_concurrent_with_progress(self):
        """Test concurrent execution with progress callback."""
        orchestrator = BatchOrchestrator(max_concurrent=2)

        tasks = [
            BaseTask(
                task_id=f"task_{i}",
                benchmark_name="test",
                description=f"Task {i}",
                language="python",
                metadata={"prompt": f"Task {i}"}
            )
            for i in range(3)
        ]

        progress_updates = []

        def progress_callback(completed, total):
            progress_updates.append((completed, total))

        mock_model_adapter = AsyncMock()
        mock_model_adapter.generate.return_value = GenerateResponse(
            content="test",
            finish_reason="stop"
        )
        mock_model_info = Mock()
        mock_model_info.name = "test-model"
        # get_model_info should not be async
        mock_model_adapter.get_model_info = Mock(return_value=mock_model_info)

        mock_benchmark_adapter = Mock()
        mock_benchmark_adapter.evaluate_task.return_value = TaskResult(
            task_id="test",
            benchmark_name="test",
            status=TaskStatus.COMPLETED,
            passed=True,
            score=0.8,
            execution_time=0.1
        )

        config = EvaluationConfig()

        results = await orchestrator._execute_tasks_concurrent(
            tasks,
            mock_model_adapter,
            mock_benchmark_adapter,
            config,
            progress_callback=progress_callback
        )

        assert len(results) == 3
        assert len(progress_updates) == 3
        assert progress_updates[-1] == (3, 3)

    def test_save_results(self):
        """Test saving results to disk."""
        orchestrator = BatchOrchestrator()

        request = EvaluationRequest(
            model_name="test-model",
            benchmark_name="test-benchmark"
        )

        task_results = [
            TaskResult(
                task_id="task_1",
                benchmark_name="test",
                status=TaskStatus.COMPLETED,
                passed=True,
                score=0.9,
                execution_time=1.0
            )
        ]

        metrics = {}
        summary = {"pass_rate": 1.0}

        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator._save_results(
                request,
                task_results,
                metrics,
                summary,
                tmpdir
            )

            # Check summary file exists
            summary_files = list(Path(tmpdir).glob("*_summary.json"))
            assert len(summary_files) == 1

            with open(summary_files[0]) as f:
                saved_summary = json.load(f)

            assert saved_summary["request"]["model_name"] == "test-model"
            assert saved_summary["summary"]["pass_rate"] == 1.0

            # Check results file exists
            results_files = list(Path(tmpdir).glob("*_results.jsonl"))
            assert len(results_files) == 1

            with open(results_files[0]) as f:
                lines = f.readlines()

            assert len(lines) == 1
            result_data = json.loads(lines[0])
            assert result_data["task_id"] == "task_1"
            assert result_data["passed"] is True

    @pytest.mark.asyncio
    async def test_run_evaluation_integration(self):
        """Test complete evaluation run (integration test)."""
        orchestrator = BatchOrchestrator(max_concurrent=2)

        request = EvaluationRequest(
            model_name="gpt-4-turbo",
            benchmark_name="lm_eval",
            task_name="single_turn_scenarios_function_generation",
            max_samples=3
        )

        # Mock model factory
        with patch.object(orchestrator.model_factory, 'get_adapter') as mock_get_model:
            mock_model_adapter = AsyncMock()
            mock_model_adapter.generate.return_value = GenerateResponse(
                content="def test(): pass",
                finish_reason="stop"
            )
            mock_model_info = Mock()
            mock_model_info.name = "test-model"
            # get_model_info should not be async
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
                        description=f"Task {i}",
                        language="python",
                        metadata={"prompt": f"Prompt {i}"}
                    )
                    for i in range(3)
                ]
                mock_benchmark.load_tasks.return_value = mock_tasks

                mock_benchmark.evaluate_task.return_value = TaskResult(
                    task_id="test",
                    benchmark_name="lm_eval",
                    status=TaskStatus.COMPLETED,
                    passed=True,
                    score=0.9,
                    execution_time=0.5
                )

                mock_get_benchmark.return_value = mock_benchmark

                # Run evaluation
                result = await orchestrator.run_evaluation(request)

                assert result.error is None
                assert len(result.task_results) == 3
                assert result.summary["total_tasks"] == 3
                assert result.total_time > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
