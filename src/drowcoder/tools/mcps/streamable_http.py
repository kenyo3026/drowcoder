import logging
import asyncio
from dataclasses import dataclass, field, asdict
from functools import wraps
from typing import Dict, Callable, Optional, Union, Any, List
from pathlib import Path

import mcp
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from .base import MCPBaseClient, MCPResponse, MCPResponseMetadata
from .utils import OpenAICompatibleDesc


@dataclass
class MCPStreamableHTTPClientConfig:
    url: str
    headers: Optional[Dict[str, str]] = field(default_factory=dict)

class MCPStreamableHTTPClient(MCPBaseClient):
    """Base class for MCP Client implementations"""

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        logger: Optional[logging.Logger] = None,
        callback: Optional[Callable] = None,
        checkpoint: Optional[Union[str, Path]] = None,
        auto_initialize: bool = True,
        **kwargs,
    ):
        """
        Initialize MCP Streamable HTTP Client.

        Args:
            url: MCP server URL
            headers: Optional HTTP headers
            logger: Optional logger instance
            callback: Optional callback function
            checkpoint: Optional checkpoint root
            auto_initialize: Whether to automatically call initialize() (default: True)
                           When True, will also load tool descriptions from the server
            **kwargs: Additional configuration parameters
        """
        # Initialize tool_descs before parent __init__ so initialize() can access it
        self.tool_descs: Optional[List[Dict[str, Any]]] = None

        # Initialize Streamable HTTP specific config before parent __init__
        # so initialize() can access it if needed
        self.config = MCPStreamableHTTPClientConfig(
            url=url,
            headers=headers or {},
        )

        # Initialize parent class (logger, callback, checkpoint, auto_initialize)
        # This may call initialize() if auto_initialize=True
        super().__init__(
            logger=logger,
            callback=callback,
            checkpoint=checkpoint,
            auto_initialize=auto_initialize,
        )

    def initialize(self) -> None:
        """
        Initialize the MCP Streamable HTTP client.

        This method loads tool descriptions from the MCP server.
        """
        # Call parent initialize first (sets _initialized flag and logs)
        super().initialize()

        # Load tool descriptions as part of initialization
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

    def is_connected(self) -> bool:
        """Check if the client is connected to the MCP server"""
        # TODO: Will be implemented in upcoming version
        return

    def with_session(self, func: Callable) -> Callable:
        """
        Decorator: Automatically handles MCP session creation and cleanup

        The decorated function will receive a session parameter
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            self.logger.info(f"Connecting to {self.config.url}...")

            try:
                # Establish Streamable HTTP connection
                # streamablehttp_client returns a tuple (read, write, callback)
                async with streamablehttp_client(**asdict(self.config)) as (read, write, _):
                    # Create client session with read and write streams
                    # Ignore the third value (callback)
                    async with ClientSession(read, write) as session:
                        # Initialize connection
                        self.logger.info("Initializing MCP session...")

                        await session.initialize()
                        self.logger.info("Session initialized successfully!\n")

                        # Execute business logic with session
                        response = await func(session, *args, **kwargs)
                        self.logger.info("\nOperation completed, closing connection...")

                        return response

            except Exception as e:
                self.logger.exception(f"Error connecting to {self.config.url}: {e}")
                raise

        return wrapper

    async def _list_tools_async(self, dump_to_openai_desc: bool = False):
        """Internal async implementation for listing tools"""
        async with streamablehttp_client(**asdict(self.config)) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()

                if dump_to_openai_desc:
                    return [
                        {
                            'type': 'function',
                            'function': asdict(OpenAICompatibleDesc.from_mcp_type_tool(tool))
                        }
                        for tool in tools_response.tools
                    ]

                return tools_response.tools

    def list_tools(self, dump_to_openai_desc: bool = False):
        """
        List all available tools from the MCP server (synchronous).

        Args:
            dump_to_openai_desc: If True, returns OpenAI-compatible format

        Returns:
            List of tool descriptions
        """
        return self._run_async(self._list_tools_async(dump_to_openai_desc))

    async def _call_tool_async(self, tool_name: str, **arguments):
        """
        Call a specific tool with given arguments (asynchronous).

        Args:
            tool_name: Name of the tool to call
            **arguments: Arguments to pass to the tool

        Returns:
            Dumped MCPResponse object (string format by default)
        """
        try:
            async with streamablehttp_client(**asdict(self.config)) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    # MCP session.call_tool expects arguments as a dict, not **kwargs
                    result = await session.call_tool(tool_name, arguments)
                    response = MCPResponse.from_call_tool_result(tool_name, result)
                    return response.dump(filter_empty_fields=True)
        except Exception as e:
            # Handle any errors during MCP tool execution
            self.logger.error(f"Error calling MCP tool '{tool_name}': {str(e)}", exc_info=True)
            error_response = MCPResponse(
                tool_name=tool_name,
                success=False,
                content=None,
                error=f"Error calling MCP tool '{tool_name}': {str(e)}",
                metadata=MCPResponseMetadata(tool_name=tool_name, is_error=True)
            )
            return error_response.dump(filter_empty_fields=True)

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