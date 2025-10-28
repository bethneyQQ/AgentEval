"""
Tests for benchmark adapters.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from core.benchmark_adapter_base import (
    AdapterInfo,
    BaseTask,
    BenchmarkAdapter,
    BenchmarkType,
    EvaluationConfig,
    TaskResult,
    TaskStatus,
    BenchmarkAdapterRegistry,
)
from core.loombench_adapter import LoomBenchAdapter, LoomBenchTask
from core.lmeval_adapter import LMEvalAdapter, LMEvalTask
from core.benchmark_registry import (
    get_adapter,
    list_adapters,
    get_adapter_info,
    register_builtin_adapters
)


class TestBenchmarkAdapterBase:
    """Tests for benchmark adapter base classes."""

    def test_task_status_enum(self):
        """Test TaskStatus enum."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.TIMEOUT.value == "timeout"
        assert TaskStatus.ERROR.value == "error"

    def test_benchmark_type_enum(self):
        """Test BenchmarkType enum."""
        assert BenchmarkType.CODE_GENERATION.value == "code_generation"
        assert BenchmarkType.BUG_FIXING.value == "bug_fixing"
        assert BenchmarkType.CODE_COMPLETION.value == "code_completion"
        assert BenchmarkType.ISSUE_RESOLUTION.value == "issue_resolution"

    def test_adapter_info_creation(self):
        """Test AdapterInfo dataclass."""
        info = AdapterInfo(
            name="test",
            version="1.0",
            benchmark_type=BenchmarkType.CODE_GENERATION,
            description="Test adapter",
            supported_languages=["python"]
        )

        assert info.name == "test"
        assert info.version == "1.0"
        assert info.benchmark_type == BenchmarkType.CODE_GENERATION
        assert not info.requires_docker
        assert not info.requires_sandbox

    def test_base_task_creation(self):
        """Test BaseTask dataclass."""
        task = BaseTask(
            task_id="test_001",
            benchmark_name="test_bench",
            description="Test task",
            language="python"
        )

        assert task.task_id == "test_001"
        assert task.benchmark_name == "test_bench"
        assert task.description == "Test task"
        assert task.language == "python"

    def test_task_result_creation(self):
        """Test TaskResult dataclass."""
        result = TaskResult(
            task_id="test_001",
            benchmark_name="test_bench",
            status=TaskStatus.COMPLETED,
            passed=True,
            score=0.95,
            execution_time=1.5
        )

        assert result.task_id == "test_001"
        assert result.status == TaskStatus.COMPLETED
        assert result.passed is True
        assert result.score == 0.95
        assert result.execution_time == 1.5

    def test_evaluation_config_defaults(self):
        """Test EvaluationConfig default values."""
        config = EvaluationConfig()

        assert config.max_samples is None
        assert config.timeout == 300
        assert config.num_workers == 1
        assert config.temperature == 0.0
        assert config.max_tokens == 4096
        assert config.enable_caching is True

    def test_adapter_registry_register(self):
        """Test registering adapters in registry."""
        registry = BenchmarkAdapterRegistry()

        class MockAdapter(BenchmarkAdapter):
            def get_adapter_info(self):
                return AdapterInfo(
                    name="mock",
                    version="1.0",
                    benchmark_type=BenchmarkType.CODE_GENERATION,
                    description="Mock",
                    supported_languages=["python"]
                )

            def initialize(self):
                pass

            def load_tasks(self, task_ids=None, max_samples=None):
                return []

            def evaluate_task(self, task, model_output, **kwargs):
                return TaskResult(
                    task_id=task.task_id,
                    benchmark_name="mock",
                    status=TaskStatus.COMPLETED,
                    passed=True,
                    score=1.0,
                    execution_time=0.1
                )

            def evaluate_batch(self, tasks, model_outputs, **kwargs):
                return []

        registry.register("mock", MockAdapter)
        assert "mock" in registry.list_adapters()

    def test_adapter_registry_get_adapter(self):
        """Test getting adapter from registry."""
        registry = BenchmarkAdapterRegistry()

        class MockAdapter(BenchmarkAdapter):
            def get_adapter_info(self):
                return AdapterInfo(
                    name="mock",
                    version="1.0",
                    benchmark_type=BenchmarkType.CODE_GENERATION,
                    description="Mock",
                    supported_languages=["python"]
                )

            def initialize(self):
                pass

            def load_tasks(self, task_ids=None, max_samples=None):
                return []

            def evaluate_task(self, task, model_output, **kwargs):
                return TaskResult(
                    task_id=task.task_id,
                    benchmark_name="mock",
                    status=TaskStatus.COMPLETED,
                    passed=True,
                    score=1.0,
                    execution_time=0.1
                )

            def evaluate_batch(self, tasks, model_outputs, **kwargs):
                return []

        registry.register("mock", MockAdapter)
        adapter = registry.get_adapter("mock")
        assert isinstance(adapter, MockAdapter)

    def test_adapter_registry_unknown_adapter(self):
        """Test getting unknown adapter raises error."""
        registry = BenchmarkAdapterRegistry()

        with pytest.raises(KeyError, match="not found"):
            registry.get_adapter("unknown")


class TestLoomBenchAdapter:
    """Tests for LoomBenchAdapter."""

    def test_loombench_task_creation(self):
        """Test LoomBenchTask creation."""
        task = LoomBenchTask(
            task_id="django__django-123",
            description="Fix bug in Django",
            language="python",
            repo="django/django",
            base_commit="abc123"
        )

        assert task.task_id == "django__django-123"
        assert task.repo == "django/django"
        assert task.base_commit == "abc123"

    def test_loombench_adapter_info(self):
        """Test LoomBenchAdapter adapter info."""
        adapter = LoomBenchAdapter()
        info = adapter.get_adapter_info()

        assert info.name == "loombench"
        assert info.benchmark_type == BenchmarkType.ISSUE_RESOLUTION
        assert "python" in info.supported_languages
        assert info.requires_docker is True

    def test_loombench_adapter_initialization(self):
        """Test LoomBenchAdapter initialization."""
        adapter = LoomBenchAdapter()

        # Should not raise error (path might not exist in test env, but that's OK)
        try:
            adapter.initialize()
        except FileNotFoundError:
            # Expected if loombench not installed
            pass

    def test_loombench_load_tasks_no_datasets(self):
        """Test loading tasks without datasets library."""
        adapter = LoomBenchAdapter()
        adapter._initialized = True

        # Mock datasets module not being available
        import sys
        original_modules = sys.modules.copy()

        # Temporarily remove datasets module if it exists
        if 'datasets' in sys.modules:
            del sys.modules['datasets']

        try:
            # This should raise ImportError if datasets is not installed
            # If datasets IS installed, we skip this test
            try:
                import datasets
                pytest.skip("datasets library is installed, skipping this test")
            except ImportError:
                with pytest.raises(ImportError):
                    adapter.load_tasks(max_samples=5)
        finally:
            # Restore original modules
            sys.modules.update(original_modules)

    def test_loombench_evaluate_task(self):
        """Test evaluating a single task."""
        adapter = LoomBenchAdapter()
        adapter._initialized = True

        task = LoomBenchTask(
            task_id="test_001",
            description="Test task",
            language="python"
        )

        # Mock evaluation
        with patch.object(adapter, '_run_evaluation') as mock_eval:
            mock_eval.return_value = {"resolved": True, "test_result": {}}

            result = adapter.evaluate_task(task, "def fix(): pass")

            assert result.task_id == "test_001"
            assert result.benchmark_name == "loombench"
            assert result.status == TaskStatus.COMPLETED


class TestLMEvalAdapter:
    """Tests for LMEvalAdapter."""

    def test_lmeval_task_creation(self):
        """Test LMEvalTask creation."""
        task = LMEvalTask(
            task_id="fg_001",
            description="Generate fibonacci function",
            language="python",
            scenario="function_generation",
            difficulty="intermediate",
            prompt="Write a function that generates fibonacci numbers"
        )

        assert task.task_id == "fg_001"
        assert task.scenario == "function_generation"
        assert task.difficulty == "intermediate"

    def test_lmeval_adapter_info(self):
        """Test LMEvalAdapter adapter info."""
        adapter = LMEvalAdapter()
        info = adapter.get_adapter_info()

        assert info.name == "lm_eval"
        assert info.benchmark_type == BenchmarkType.CODE_GENERATION
        assert "python" in info.supported_languages

    def test_lmeval_adapter_initialization(self):
        """Test LMEvalAdapter initialization."""
        adapter = LMEvalAdapter()

        try:
            adapter.initialize()
        except FileNotFoundError:
            # Expected if lm_eval not installed
            pass

    def test_lmeval_evaluate_code_syntax_valid(self):
        """Test code evaluation with syntactically valid code."""
        adapter = LMEvalAdapter()

        task = LMEvalTask(
            task_id="test_001",
            description="Test",
            language="python",
            scenario="function_generation",
            difficulty="simple",
            prompt="Test"
        )

        code = "def hello():\n    print('Hello')"
        metrics = adapter._evaluate_code(task, code)

        assert metrics['syntax_validity'] == 1.0
        assert metrics['runtime_correctness'] == 1.0

    def test_lmeval_evaluate_code_syntax_invalid(self):
        """Test code evaluation with syntactically invalid code."""
        adapter = LMEvalAdapter()

        task = LMEvalTask(
            task_id="test_001",
            description="Test",
            language="python",
            scenario="function_generation",
            difficulty="simple",
            prompt="Test"
        )

        code = "def hello(\n    print('Hello')"
        metrics = adapter._evaluate_code(task, code)

        assert metrics['syntax_validity'] == 0.0

    def test_lmeval_calculate_score(self):
        """Test score calculation."""
        adapter = LMEvalAdapter()

        metrics = {
            'syntax_validity': 1.0,
            'runtime_correctness': 1.0,
            'exact_match': 0.0,
            'code_quality': 0.5
        }

        score = adapter._calculate_score(metrics)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be high since syntax and runtime are perfect

    def test_lmeval_evaluate_task(self):
        """Test evaluating a single task."""
        adapter = LMEvalAdapter()
        adapter._initialized = True

        task = LMEvalTask(
            task_id="test_001",
            description="Test",
            language="python",
            scenario="function_generation",
            difficulty="simple",
            prompt="Write hello function"
        )

        code = "def hello():\n    print('Hello World')"
        result = adapter.evaluate_task(task, code)

        assert result.task_id == "test_001"
        assert result.benchmark_name == "lm_eval"
        assert result.status == TaskStatus.COMPLETED
        assert result.score >= 0.0

    def test_lmeval_evaluate_batch(self):
        """Test batch evaluation."""
        adapter = LMEvalAdapter()
        adapter._initialized = True

        tasks = [
            LMEvalTask(
                task_id=f"test_{i}",
                description="Test",
                language="python",
                scenario="function_generation",
                difficulty="simple",
                prompt="Test"
            )
            for i in range(3)
        ]

        outputs = [
            "def func1(): pass",
            "def func2(): pass",
            "def func3(): pass"
        ]

        results = adapter.evaluate_batch(tasks, outputs)
        assert len(results) == 3
        assert all(r.status == TaskStatus.COMPLETED for r in results)


class TestBenchmarkRegistry:
    """Tests for benchmark registry."""

    def test_list_adapters(self):
        """Test listing available adapters."""
        adapters = list_adapters()
        assert isinstance(adapters, list)
        assert "loombench" in adapters
        assert "lm_eval" in adapters

    def test_get_adapter_lm_eval(self):
        """Test getting lm_eval adapter."""
        adapter = get_adapter("lm_eval")
        assert isinstance(adapter, LMEvalAdapter)

    def test_get_adapter_loombench(self):
        """Test getting loombench adapter."""
        adapter = get_adapter("loombench")
        assert isinstance(adapter, LoomBenchAdapter)

    def test_get_adapter_with_config(self):
        """Test getting adapter with custom config."""
        config = EvaluationConfig(max_samples=10, timeout=600)
        adapter = get_adapter("lm_eval", config=config)

        assert adapter.config.max_samples == 10
        assert adapter.config.timeout == 600

    def test_get_adapter_info(self):
        """Test getting adapter info."""
        info = get_adapter_info("lm_eval")

        assert isinstance(info, dict)
        assert info["name"] == "lm_eval"
        assert "version" in info
        assert "benchmark_type" in info
        assert "description" in info

    def test_get_unknown_adapter(self):
        """Test getting unknown adapter raises error."""
        with pytest.raises(KeyError):
            get_adapter("unknown_adapter")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
