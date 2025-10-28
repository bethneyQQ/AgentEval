"""
Benchmark adapter registry and initialization.

This module provides a centralized registry for all benchmark adapters
and convenient functions to access them.
"""

from typing import Dict, List, Optional

from core.benchmark_adapter_base import (
    BenchmarkAdapter,
    BenchmarkAdapterRegistry,
    EvaluationConfig,
    global_adapter_registry
)
from core.loombench_adapter import LoomBenchAdapter
from core.lmeval_adapter import LMEvalAdapter


def register_builtin_adapters() -> None:
    """Register all built-in benchmark adapters."""
    global_adapter_registry.register("loombench", LoomBenchAdapter)
    global_adapter_registry.register("lm_eval", LMEvalAdapter)


def get_adapter(
    name: str,
    config: Optional[EvaluationConfig] = None,
    **adapter_kwargs
) -> BenchmarkAdapter:
    """
    Get a benchmark adapter by name.

    Args:
        name: Name of the adapter ('loombench' or 'lm_eval')
        config: Evaluation configuration
        **adapter_kwargs: Additional keyword arguments for the adapter

    Returns:
        Instance of the requested adapter

    Examples:
        >>> adapter = get_adapter("lm_eval", task_name="single_turn_scenarios_function_generation")
        >>> adapter = get_adapter("loombench", dataset_name="princeton-nlp/SWE-bench_Lite")
    """
    # Create adapter with config
    adapter_class = global_adapter_registry._adapters.get(name)
    if adapter_class is None:
        raise KeyError(
            f"Adapter '{name}' not found. "
            f"Available adapters: {list_adapters()}"
        )

    return adapter_class(config=config, **adapter_kwargs)


def list_adapters() -> List[str]:
    """
    List all available benchmark adapters.

    Returns:
        List of adapter names
    """
    return global_adapter_registry.list_adapters()


def get_adapter_info(name: str) -> Dict:
    """
    Get information about a benchmark adapter.

    Args:
        name: Name of the adapter

    Returns:
        Dictionary with adapter information
    """
    adapter = get_adapter(name)
    info = adapter.get_adapter_info()

    return {
        "name": info.name,
        "version": info.version,
        "benchmark_type": info.benchmark_type.value,
        "description": info.description,
        "supported_languages": info.supported_languages,
        "requires_docker": info.requires_docker,
        "requires_sandbox": info.requires_sandbox,
        "metadata": info.metadata
    }


# Register built-in adapters on module import
register_builtin_adapters()


# Convenience exports
__all__ = [
    "get_adapter",
    "list_adapters",
    "get_adapter_info",
    "register_builtin_adapters",
    "global_adapter_registry"
]
