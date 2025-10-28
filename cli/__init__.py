"""
Multi-Turn Evaluation Engine CLI Package

Command-line interface for multi-turn evaluation capabilities.
"""

# Lazy imports to avoid import errors
__all__ = [
    'MultiTurnCLI',
    'ConfigParser',
    'InteractiveMonitor'
]

def __getattr__(name):
    """Lazy import for CLI modules."""
    if name == 'MultiTurnCLI':
        from .multi_turn_cli import MultiTurnCLI
        return MultiTurnCLI
    elif name == 'ConfigParser':
        from .config_parser import ConfigParser
        return ConfigParser
    elif name == 'InteractiveMonitor':
        from .interactive_monitor import InteractiveMonitor
        return InteractiveMonitor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")