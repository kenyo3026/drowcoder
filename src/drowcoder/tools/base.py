"""
Base classes for unified tool architecture.

This module provides the abstract base classes and common data structures
for all tools in the drowcoder system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable, Union
from pathlib import Path
import logging


@dataclass
class ToolConfig:
    """
    Base configuration for all tools.

    Attributes:
        name: Tool name identifier
        logger: Optional logger instance for tool operations
        callback: Optional callback function for tool events
        checkpoint_path: Optional checkpoint path for tools that need persistence
    """
    logger: Optional[logging.Logger] = None
    callback: Optional[Callable] = None
    checkpoint_path: Optional[Union[str, Path]] = None


@dataclass
class ToolResult:
    """
    Standard result format for all tool executions.

    Attributes:
        success: Whether the tool execution succeeded
        data: The actual result data from the tool
        error: Error message if execution failed
        metadata: Additional metadata about the execution
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """
    Abstract base class for all tools.

    All tools should inherit from this class and implement the execute() method.
    This ensures a consistent interface across all tools and enables unified
    initialization and management.
    """
    name = 'base'

    def __init__(self, config: Optional[ToolConfig] = None, auto_initialize: bool = True, **kwargs):
        """
        Initialize the tool with configuration.

        Args:
            config: Optional ToolConfig instance. If None, creates one from kwargs.
            auto_initialize: Whether to automatically call initialize() (default: True)
            **kwargs: Configuration parameters matching ToolConfig fields:
                - name: Tool name identifier (defaults to class name)
                - logger: Optional logger instance for tool operations
                - callback: Optional callback function for tool events
                - checkpoint_path: Optional checkpoint path for persistence
        """
        # Always create a fresh ToolConfig from kwargs
        # This simplifies the logic and avoids dataclass replace issues
        config = ToolConfig(**kwargs)

        # Set all config attributes as instance attributes directly
        for key, value in config.__dict__.items():
            setattr(self, key, value)

        if self.logger is None:
            self.logger = logging.getLogger(self.__class__.__name__)

        self._initialized = False

        # Auto-initialize by default for convenience
        if auto_initialize:
            self.initialize()

    def initialize(self) -> None:
        """
        Initialize the tool.

        Called automatically in __init__ unless auto_initialize=False.
        Subclasses can override to add custom initialization logic,
        but should call super().initialize().

        This method is idempotent - calling it multiple times is safe.
        """
        if self._initialized:
            self.logger.debug(f"Tool {self.name} already initialized, skipping")
            return

        self._initialized = True
        self.logger.info(f"Tool {self.name} initialized")

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool's main functionality.

        Args:
            **kwargs: Tool-specific execution parameters

        Returns:
            ToolResult with execution results
        """
        pass

    def _validate_initialized(self) -> None:
        """
        Validate that the tool has been initialized.

        Raises:
            RuntimeError: If tool has not been initialized
        """
        if not self._initialized:
            raise RuntimeError(
                f"Tool {self.name} not initialized. "
                f"Call initialize() before execute(), or use auto_initialize=True (default)."
            )

    def _trigger_callback(self, event: str, data: Dict[str, Any]) -> None:
        """
        Trigger the callback if one is configured.

        Args:
            event: Event name
            data: Event data
        """
        if self.callback:
            try:
                self.callback(event, data)
            except Exception as e:
                self.logger.warning(f"Callback failed for event {event}: {e}")

