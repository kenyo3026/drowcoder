"""
drowcoder - A powerful agentic AI coding assistant framework for Cursor IDE

This package provides a comprehensive framework for building AI coding assistants
with tool management, checkpoint system, and extensible architecture.
"""

__version__ = "0.1.0"
__author__ = "kenyo3026"
__email__ = "kenyo3026@gmail.com"

from .agent import DrowAgent, AgentRole, ToolCallResponse
from .checkpoint import Checkpoint
from .verbose import VerboseStyle, VerboserFactory
from .prompts import SystemPromptInstruction

__all__ = [
    "DrowAgent",
    "AgentRole",
    "ToolCallResponse",
    "Checkpoint",
    "ToolConfig",
    "VerboseStyle",
    "VerboserFactory",
    "SystemPromptInstruction",
    "__version__",
]
