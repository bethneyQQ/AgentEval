#!/usr/bin/env python3
"""
Command-line utility for listing available models and benchmarks.
"""

import argparse
import sys
from pathlib import Path

from core.model_adapter_factory import ModelAdapterFactory
from core.benchmark_registry import list_adapters, get_adapter_info


def list_models() -> None:
    """List all available models."""
    print("\nAvailable Models:")
    print("-" * 80)

    factory = ModelAdapterFactory()

    # Try to load config file
    config_path = Path(__file__).parent.parent / "config" / "models.yaml"

    if not config_path.exists():
        print("  No models.yaml configuration file found")
        print(f"  Expected location: {config_path}")
        print("\n  Default supported model providers:")
        print("    - OpenAI (gpt-4-turbo, gpt-3.5-turbo, etc.)")
        print("    - Anthropic (claude-3-opus-20240229, claude-3-sonnet-20240229, etc.)")
        print("    - Google (gemini-pro, gemini-1.5-pro, etc.)")
        print("    - And many more via LiteLLM")
        return

    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)

        if not config or 'models' not in config:
            print("  No models configured in models.yaml")
            return

        for model_name, model_config in config['models'].items():
            provider = model_config.get('provider', 'unknown')
            model_id = model_config.get('model_id', model_name)
            description = model_config.get('description', '')

            print(f"\n  {model_name}")
            print(f"    Provider: {provider}")
            print(f"    Model ID: {model_id}")
            if description:
                print(f"    Description: {description}")

        print()

    except Exception as e:
        print(f"  Error loading models configuration: {e}")


def list_benchmarks() -> None:
    """List all available benchmarks."""
    print("\nAvailable Benchmarks:")
    print("-" * 80)

    adapters = list_adapters()

    if not adapters:
        print("  No benchmarks registered")
        return

    for adapter_name in adapters:
        try:
            info = get_adapter_info(adapter_name)
            print(f"\n  {adapter_name}")
            print(f"    Name: {info.name}")
            print(f"    Version: {info.version}")
            print(f"    Description: {info.description}")
            print(f"    Supported types: {', '.join([t.value for t in info.supported_types])}")
        except Exception as e:
            print(f"\n  {adapter_name}")
            print(f"    Error: {e}")

    print()


def list_all() -> None:
    """List all available resources."""
    list_models()
    print()
    list_benchmarks()


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='List available models and benchmarks for evaluation',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'resource',
        nargs='?',
        choices=['models', 'benchmarks', 'all'],
        default='all',
        help='Resource type to list (default: all)'
    )

    return parser.parse_args()


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code
    """
    args = parse_args()

    try:
        if args.resource == 'models':
            list_models()
        elif args.resource == 'benchmarks':
            list_benchmarks()
        else:
            list_all()

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
