import logging
from abc import ABC, abstractmethod
from typing import Dict, Callable, Optional, Union
from pathlib import Path


# @dataclass
# class MCPClientConfig:
#     """
#     Base configuration for all tools.

#     Attributes:
#         logger: Optional logger instance for tool operations
#         callback: Optional callback function for tool events
#         checkpoint: Optional checkpoint root for tools that need persistence
#     """
#     logger: Optional[logging.Logger] = None
#     callback: Optional[Callable] = None
#     checkpoint: Optional[Union[str, Path]] = None

# @dataclass
# class MCPBaseClientConnectionConfig:

#     # for stdio
#     command: str = None,
#     args: Optional[List] = field(default_factory=list),
#     env: Optional[Dict] = field(default_factory=dict),

#     # for streamable http
#     url: str = None
#     headers: Optional[Dict[str, str]] = field(default_factory=dict)

class MCPBaseClient(ABC):
    """Base class for MCP Client implementations"""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        callback: Optional[Callable] = None,
        checkpoint: Optional[Union[str, Path]] = None,
        **kwargs,
    ):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.callback = callback
        self.checkpoint = checkpoint

    @classmethod
    def from_dict(cls, data: Dict) -> "MCPBaseClient":
        """Create instance from dictionary"""
        return cls(**data)

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the client is connected to the MCP server"""
        # TODO: Will be implemented in upcoming version
        ...

    @abstractmethod
    def with_session(self, func: Callable) -> Callable:
        """
        Decorator: Automatically handles MCP session creation and cleanup

        The decorated function will receive a session parameter
        """
        # TODO: Will be implemented in upcoming version
        ...

    def list_tools(self):
        ...

    def call_tool(self):
        ...

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