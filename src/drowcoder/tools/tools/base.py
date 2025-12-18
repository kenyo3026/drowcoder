"""
Base classes for unified tool architecture.

This module provides the abstract base classes and common data structures
for all tools in the drowcoder system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, Callable, Union
from pathlib import Path
import logging


@dataclass
class ToolResponseMetadata:
    """
    Base metadata for tool execution responses.

    This class provides common metadata fields that can be included in tool responses.
    Individual tools can subclass this to add tool-specific metadata fields.

    Attributes:
        tool_name: Name of the tool that generated this response
        execution_time_ms: Time taken to execute the tool in milliseconds
    """

class _IntactType:
    """Unique sentinel class for INTACT response type."""
    pass

INTACT = _IntactType()

@dataclass(frozen=True)
class ToolResponseType:
    """
    Response type constants for ToolResponse conversion.
    """
    INTACT     :str = INTACT
    DICT       :str = 'dict'
    STR        :str = 'str'
    PRETTY_STR :str = 'pretty_str'

@dataclass
class ToolResponse:
    """
    Standard response format for all tool executions.

    This class provides a consistent structure for all tool responses, ensuring
    uniform handling of success/failure cases and metadata across the system.

    Attributes:
        success: Whether the tool execution succeeded
        content: The actual content data from the tool. Can be any type depending
                on the specific tool (str, dict, list, etc.)
        error: Error message if execution failed. Should be None when success=True
        metadata: Optional metadata about the execution. Can be a ToolResponseMetadata
                 instance or a tool-specific subclass with additional fields
    """
    tool_name: Optional[str] = None
    success: Optional[bool] = None
    content: Any = None
    error: Optional[str] = None
    metadata: Optional[ToolResponseMetadata] = None

    def _is_empty(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, (str, bytes, bytearray)):
            return len(value) == 0
        if isinstance(value, (list, tuple, dict, set, frozenset)):
            return len(value) == 0
        return False

    def dump(
        self,
        as_type: Union[str, _IntactType] = ToolResponseType.PRETTY_STR,
        **kwargs,
    ) -> Any:
        """
        Convert ToolResponse to different output formats.

        Args:
            as_type: Output format type. Can be:
                - ToolResponseType.INTACT or INTACT: Return self as-is
                - ToolResponseType.DICT or 'dict': Convert to dictionary
                - ToolResponseType.STR or 'str': Convert to string
                - ToolResponseType.PRETTY_STR or 'pretty_str': Convert to formatted string
            **kwargs: Additional arguments passed to conversion methods

        Returns:
            Converted response based on as_type

        Examples:
            >>> response.dump(ToolResponseType.DICT)
            >>> response.dump('dict')
            >>> response.dump(ToolResponseType.PRETTY_STR, filter_empty_fields=True)
            >>> response.dump(INTACT)  # Returns self
        """
        # Normalize string input to lowercase
        if isinstance(as_type, str):
            as_type = as_type.lower()

        # Use match statement for clean pattern matching
        match as_type:
            case _ if as_type is ToolResponseType.INTACT or isinstance(as_type, _IntactType):
                return self
            case ToolResponseType.DICT | 'dict':
                return self.to_dict()
            case ToolResponseType.STR | 'str':
                return self.to_str()
            case ToolResponseType.PRETTY_STR | 'pretty_str':
                return self.to_pretty_str(**kwargs)
            case _:
                raise ValueError(
                    f"Invalid as_type: {as_type}. "
                    f"Expected ToolResponseType constant, INTACT, or string in "
                    f"['dict', 'str', 'pretty_str']"
                )

    def to_dict(self):
        """Convert ToolResponse to dictionary."""
        return asdict(self)

    def to_str(self):
        """Convert ToolResponse to string representation."""
        _dict = self.to_dict()
        return str(_dict)

    def to_pretty_str(
        self,
        filter_empty_fields: bool = False,
        filter_metadata_fields: bool = False,
    ) -> str:
        """
        Convert ToolResponse to formatted string.

        Args:
            filter_empty_fields: If True, exclude empty fields from output
            filter_metadata_fields: If True, exclude metadata field from output

        Returns:
            Formatted string with key-value pairs
        """
        _dict = self.to_dict()

        if filter_metadata_fields:
            _dict.pop('metadata', None)

        if filter_empty_fields:
            _dict = {key: value for key, value in _dict.items()
                    if not self._is_empty(value)}

        return '\n'.join(
            [f'{key}: {str(value)}' for key, value in _dict.items()]
        )


class BaseTool(ABC):
    """
    Abstract base class for all tools.

    All tools should inherit from this class and implement the execute() method.
    This ensures a consistent interface across all tools and enables unified
    initialization and management.
    """
    name = 'base'
    dumping_fields = {'as_type', 'filter_empty_fields', 'filter_metadata_fields'}

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        callback: Optional[Callable] = None,
        checkpoint: Optional[Union[str, Path]] = None,
        auto_initialize: bool = True,
        **kwargs
    ):
        """
        Initialize the tool with configuration.

        Args:
            logger: Optional logger instance for tool operations.
                If None, creates a logger with the class name.
            callback: Optional callback function for tool events
            checkpoint: Optional checkpoint root for persistence
            auto_initialize: Whether to automatically call initialize() (default: True)
            **kwargs: Additional keyword arguments (for subclasses to extend)
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.callback = callback
        self.checkpoint = checkpoint

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
    def execute(
        self,
        as_type: Union[str, _IntactType] = ToolResponseType.PRETTY_STR,
        filter_empty_fields: bool = True,
        filter_metadata_fields: bool = True,
        **kwargs,
    ) -> ToolResponse:
        """
        Execute the tool's main functionality.

        Args:
            as_type: Output format type for the response
            filter_empty_fields: Whether to filter empty fields in output
            filter_metadata_fields: Whether to filter metadata fields in output
            **kwargs: Tool-specific execution parameters

        Returns:
            ToolResponse (or converted format based on as_type)
        """
        pass

    def _parse_dump_kwargs(self, local_vars: Dict[str, Any], invert: bool = False) -> Dict[str, Any]:
        """
        Parse dumping-related kwargs from local variables.

        Args:
            local_vars: Dictionary of local variables (typically from locals())
            invert: If False, return only dumping fields; if True, return non-dumping fields

        Returns:
            Filtered dictionary of kwargs
        """
        # Remove 'self' and 'kwargs' from local_vars
        filtered = {k: v for k, v in local_vars.items() if k not in {'self', 'kwargs'}}

        if invert:
            # Return non-dumping fields (tool-specific parameters)
            return {k: v for k, v in filtered.items() if k not in self.dumping_fields}
        else:
            # Return only dumping fields
            return {k: v for k, v in filtered.items() if k in self.dumping_fields}

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

