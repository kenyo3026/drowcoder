"""
Tool Factory for managing predefined tool sets.

This module provides ToolType (enum-like constants) and ToolFactory
for managing different tool configurations based on roles.
"""

import pathlib
from dataclasses import dataclass


DEFAULT_TOOL_CONFIG_ROOT = pathlib.Path(__file__).resolve().parent

@dataclass(frozen=True)
class ToolType:
    """Tool type constants (enum-like)."""
    EMPTY: str = 'EMPTY'
    CODER: str = 'CODER'

class ToolFactory:
    """Factory for predefined tool sets."""
    EMPTY: list = []
    CODER: list = [
        str(DEFAULT_TOOL_CONFIG_ROOT / yaml)
        for yaml in [
            'attempt_completion.yaml',
            'bash.yaml',
            'load.yaml',
            'search_and_replace.yaml',
            'search.yaml',
            'write.yaml',
            'todo.yaml',
        ]
    ]
