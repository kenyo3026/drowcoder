import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Callable, Optional, Union
from pathlib import Path


@dataclass
class MCPResponseMetadata:
    """
    Base metadata for MCP execution responses.

    This class provides common metadata fields that can be included in MCP responses.

    Attributes:
        tool_name: Name of the MCP tool that generated this response
        is_error: Whether the response is an error (from MCP protocol)
        execution_time_ms: Time taken to execute the MCP tool in milliseconds
    """
    tool_name: Optional[str] = None
    is_error: Optional[bool] = None
    execution_time_ms: Optional[float] = None


class _IntactType:
    """Unique sentinel class for INTACT response type."""
    pass

INTACT = _IntactType()


@dataclass(frozen=True)
class MCPResponseType:
    """
    Response type constants for MCPResponse conversion.
    """
    INTACT     :str = INTACT
    DICT       :str = 'dict'
    STR        :str = 'str'
    PRETTY_STR :str = 'pretty_str'


@dataclass
class MCPResponse:
    """
    Standard response format for all MCP tool executions.

    This class provides a consistent structure for all MCP responses, ensuring
    uniform handling of success/failure cases and metadata across the system.
    It is designed to mirror ToolResponse structure while accommodating MCP-specific fields.

    Attributes:
        tool_name: Name of the MCP tool that generated this response
        success: Whether the MCP tool execution succeeded
        content: The actual content data from the MCP tool. Can be any type depending
                on the specific tool (str, dict, list, etc.)
        error: Error message if execution failed. Should be None when success=True
        metadata: Optional metadata about the execution (MCPResponseMetadata instance)
        images: Optional list of image data from MCP response
        resources: Optional list of resource references from MCP response
    """
    tool_name: Optional[str] = None
    success: Optional[bool] = None
    content: Any = None
    error: Optional[str] = None
    metadata: Optional[MCPResponseMetadata] = None
    images: Optional[List[Dict[str, Any]]] = None
    resources: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_call_tool_result(
        cls,
        tool_name: str,
        result: Any,
    ) -> "MCPResponse":
        """
        Create MCPResponse from mcp.types.CallToolResult.

        Args:
            result: CallToolResult object from MCP SDK
            tool_name: Optional tool name to include in response

        Returns:
            MCPResponse instance with extracted data
        """
        # Import here to avoid circular dependency
        try:
            from mcp.types import CallToolResult, TextContent, ImageContent, EmbeddedResource
        except ImportError:
            raise ImportError("mcp package is required for from_call_tool_response")

        # Handle case where result is None or not a CallToolResult
        if result is None:
            return cls(
                tool_name=tool_name,
                success=False,
                content=None,
                error="MCP tool returned None result",
                metadata=MCPResponseMetadata(tool_name=tool_name, is_error=True)
            )

        if not isinstance(result, CallToolResult):
            # If it's already a string or other type, wrap it
            return cls(
                tool_name=tool_name,
                success=True,
                content=str(result),
                error=None,
                metadata=MCPResponseMetadata(tool_name=tool_name, is_error=False)
            )

        # Extract content from CallToolResult
        content_parts = []
        images = []
        resources = []
        is_error = getattr(result, 'isError', False)

        if hasattr(result, 'content') and result.content:
            for item in result.content:
                if isinstance(item, TextContent):
                    content_parts.append(item.text)
                elif isinstance(item, ImageContent):
                    images.append({
                        'data': item.data,
                        'mimeType': item.mimeType
                    })
                elif isinstance(item, EmbeddedResource):
                    resources.append({
                        'type': item.type,
                        'resource': item.resource
                    })
                else:
                    # Fallback for unknown content types
                    content_parts.append(str(item))

        # Combine text content
        combined_content = '\n'.join(content_parts) if content_parts else None

        return cls(
            tool_name=tool_name,
            success=not is_error,
            content=combined_content,
            error=combined_content if is_error else None,
            metadata=MCPResponseMetadata(tool_name=tool_name, is_error=is_error),
            images=images if images else None,
            resources=resources if resources else None
        )

    def _is_empty(self, value: Any) -> bool:
        """Check if a value is considered empty."""
        if value is None:
            return True
        if isinstance(value, (str, bytes, bytearray)):
            return len(value) == 0
        if isinstance(value, (list, tuple, dict, set, frozenset)):
            return len(value) == 0
        return False

    def dump(
        self,
        as_type: Union[str, _IntactType] = MCPResponseType.PRETTY_STR,
        **kwargs,
    ) -> Any:
        """
        Convert MCPResponse to different output formats.

        Args:
            as_type: Output format type. Can be:
                - MCPResponseType.INTACT or INTACT: Return self as-is
                - MCPResponseType.DICT or 'dict': Convert to dictionary
                - MCPResponseType.STR or 'str': Convert to string
                - MCPResponseType.PRETTY_STR or 'pretty_str': Convert to formatted string
            **kwargs: Additional arguments passed to conversion methods

        Returns:
            Converted response based on as_type

        Examples:
            >>> response.dump(MCPResponseType.DICT)
            >>> response.dump('dict')
            >>> response.dump(MCPResponseType.PRETTY_STR, filter_empty_fields=True)
            >>> response.dump(INTACT)  # Returns self
        """
        # Normalize string input to lowercase
        if isinstance(as_type, str):
            as_type = as_type.lower()

        # Use match statement for clean pattern matching
        match as_type:
            case _ if as_type is MCPResponseType.INTACT or isinstance(as_type, _IntactType):
                return self
            case MCPResponseType.DICT | 'dict':
                return self.to_dict()
            case MCPResponseType.STR | 'str':
                return self.to_str()
            case MCPResponseType.PRETTY_STR | 'pretty_str':
                return self.to_pretty_str(**kwargs)
            case _:
                raise ValueError(
                    f"Invalid as_type: {as_type}. "
                    f"Expected MCPResponseType constant, INTACT, or string in "
                    f"['dict', 'str', 'pretty_str']"
                )

    def to_dict(self) -> Dict[str, Any]:
        """Convert MCPResponse to dictionary."""
        return asdict(self)

    def to_str(self) -> str:
        """Convert MCPResponse to string representation."""
        _dict = self.to_dict()
        return str(_dict)

    def to_pretty_str(
        self,
        filter_empty_fields: bool = False,
        filter_metadata_fields: bool = False,
    ) -> str:
        """
        Convert MCPResponse to formatted string.

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

class MCPBaseClient(ABC):
    """Base class for MCP Client implementations"""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        callback: Optional[Callable] = None,
        checkpoint: Optional[Union[str, Path]] = None,
        auto_initialize: bool = True,
        **kwargs,
    ):
        """
        Initialize the MCP client with configuration.

        Args:
            logger: Optional logger instance for MCP operations
            callback: Optional callback function for MCP events
            checkpoint: Optional checkpoint root for persistence
            auto_initialize: Whether to automatically call initialize() (default: True)
            **kwargs: Additional configuration parameters
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.callback = callback
        self.checkpoint = checkpoint

        self._initialized = False

        # Auto-initialize by default for convenience
        if auto_initialize:
            self.initialize()

    @classmethod
    def from_dict(cls, data: Dict) -> "MCPBaseClient":
        """Create instance from dictionary"""
        return cls(**data)

    def initialize(self) -> None:
        """
        Initialize the MCP client.

        Called automatically in __init__ unless auto_initialize=False.
        Subclasses can override to add custom initialization logic,
        but should call super().initialize().

        This method is idempotent - calling it multiple times is safe.
        """
        if self._initialized:
            self.logger.debug(f"MCP client {self.__class__.__name__} already initialized, skipping")
            return

        self._initialized = True
        self.logger.info(f"MCP client {self.__class__.__name__} initialized")

        self._load_tool_descs()

    def _load_tool_descs(self) -> None:
        """Load tool descriptions from MCP server."""
        try:
            self.tool_descs = self.list_tools(dump_to_openai_desc=True)
            if self.tool_descs:
                self.logger.debug(f"Loaded {len(self.tool_descs)} tool descriptions from MCP server")
        except Exception as e:
            self.logger.warning(f"Failed to load tool descriptions: {str(e)}", exc_info=True)
            self.tool_descs = []

    def is_connected(self) -> bool:
        """Check if the client is connected to the MCP server"""
        # TODO: Will be implemented in upcoming version
        return

    def _run_async(self, coro):
        """
        Safely run async coroutine in sync context.
        Handles both cases: with and without existing event loop.
        """
        try:
            # Try to get existing event loop (works in Jupyter, asyncio.run context, etc.)
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, try to use nest_asyncio if available
                # nest_asyncio allows nested event loops (common in Jupyter)
                try:
                    import nest_asyncio
                    # nest_asyncio.apply() should be called once at module level
                    # If not applied yet, apply it here
                    try:
                        nest_asyncio.apply()
                    except RuntimeError:
                        # Already applied, continue
                        pass
                    # After applying nest_asyncio, we can use run_until_complete
                    # even in a running loop
                    return loop.run_until_complete(coro)
                except (ImportError, RuntimeError):
                    # Fallback: create new event loop in thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, coro)
                        return future.result()
            else:
                # Loop exists but not running, use run_until_complete
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop exists, create new one
            return asyncio.run(coro)

    @abstractmethod
    def with_session(self, func: Callable) -> Callable:
        """
        Decorator: Automatically handles MCP session creation and cleanup

        The decorated function will receive a session parameter
        """
        # TODO: Will be implemented in upcoming version
        ...

    @abstractmethod
    async def _list_tools_async(self, dump_to_openai_desc: bool = False):
        ...

    def list_tools(self, dump_to_openai_desc: bool = False):
        """
        List all available tools from the MCP server (synchronous).

        Args:
            dump_to_openai_desc: If True, returns OpenAI-compatible format

        Returns:
            List of tool descriptions
        """
        return self._run_async(self._list_tools_async(dump_to_openai_desc))

    @abstractmethod
    async def _call_tool_async(self, tool_name: str, **arguments):
        ...

    def call_tool(self, tool_name: str, **arguments):
        """
        Call a specific tool with given arguments (synchronous).

        Args:
            tool_name: Name of the tool to call
            **arguments: Arguments to pass to the tool

        Returns:
            MCPResponse object with standardized format
        """
        return self._run_async(self._call_tool_async(tool_name, **arguments))

    # TODO
    # Available methods:
    # - call_tool
    # - complete
    # - get_prompt
    # - get_server_capabilities
    # - initialize
    # - list_prompts
    # - list_resource_templates
    # - list_resources
    # - list_tools
    # - read_resource
    # - send_notification
    # - send_ping
    # - send_progress_notification
    # - send_request
    # - send_roots_list_changed
    # - set_logging_level
    # - subscribe_resource
    # - unsubscribe_resource