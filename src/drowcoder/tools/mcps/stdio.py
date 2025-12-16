import logging
from dataclasses import dataclass, field, asdict
from functools import wraps
from typing import Any, Dict, List, Callable, Optional, Union, Literal
from pathlib import Path

import mcp
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .base import MCPBaseClient, MCPResponse, MCPResponseMetadata
from .utils import OpenAICompatibleDesc

@dataclass
class MCPStdioClientConfig:
    command: Optional[str] = None
    args: Optional[List[str]] = field(default_factory=list)
    env: Optional[Dict[str, str]] = field(default_factory=dict)
    cwd: Optional[Union[str, Path]] = None
    encoding: str = "utf-8"
    encoding_error_handler: Literal["strict", "ignore", "replace"] = "strict"

class MCPStdioClient(MCPBaseClient):
    """MCP Stdio Client implementation"""
    name = 'stdio'

    def __init__(
        self,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[Union[str, Path]] = None,
        encoding: str = "utf-8",
        encoding_error_handler: Literal["strict", "ignore", "replace"] = "strict",
        server_name: str = None,
        logger: Optional[logging.Logger] = None,
        callback: Optional[Callable] = None,
        checkpoint: Optional[Union[str, Path]] = None,
        auto_initialize: bool = True,
        **kwargs,
    ):
        """
        Initialize MCP Stdio Client.

        Args:
            command: Command to execute to start the MCP server
            args: Optional command line arguments
            env: Optional environment variables
            cwd: Optional working directory for the process
            encoding: Text encoding for messages (default: "utf-8")
            encoding_error_handler: Encoding error handler (default: "strict")
            server_name: Optional server name for identification (defaults to command + args)
            logger: Optional logger instance
            callback: Optional callback function
            checkpoint: Optional checkpoint root
            auto_initialize: Whether to automatically call initialize() (default: True)
                           When True, will also load tool descriptions from the server
            **kwargs: Additional configuration parameters
        """
        # Initialize tool_descs before parent __init__ so initialize() can access it
        self.tool_descs: Optional[List[Dict[str, Any]]] = None

        # Initialize Stdio specific config before parent __init__
        # so initialize() can access it if needed
        self.config = MCPStdioClientConfig(
            command=command,
            args=args or [],
            env=env,
            cwd=cwd,
            encoding=encoding,
            encoding_error_handler=encoding_error_handler,
        )

        # Initialize parent class (logger, callback, checkpoint, auto_initialize)
        # This may call initialize() if auto_initialize=True
        super().__init__(
            server_name=server_name or (f'{command} {" ".join(args)}' if command else ''),
            logger=logger,
            callback=callback,
            checkpoint=checkpoint,
            auto_initialize=auto_initialize,
        )

    def with_session(self, func: Callable) -> Callable:
        """
        Decorator: Automatically handles MCP session creation and cleanup

        The decorated function will receive a session parameter
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            self.logger.info(f"Execute {self.config.command}...")

            # Create StdioServerParameters object from config
            stdio_params = StdioServerParameters(
                command=self.config.command,
                args=self.config.args,
                env=self.config.env,
                cwd=self.config.cwd,
                encoding=self.config.encoding,
                encoding_error_handler=self.config.encoding_error_handler,
            )

            try:
                # stdio_client returns a tuple (read, write)
                async with stdio_client(stdio_params) as (read, write):
                    # Create client session with read and write streams
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
                self.logger.exception(f"Error connecting to {self.config.command}: {e}")
                raise

        return wrapper

    async def _list_tools_async(self, dump_to_openai_desc: bool = False):
        """Internal async implementation for listing tools"""
        # Create StdioServerParameters object from config
        stdio_params = StdioServerParameters(
            command=self.config.command,
            args=self.config.args,
            env=self.config.env,
            cwd=self.config.cwd,
            encoding=self.config.encoding,
            encoding_error_handler=self.config.encoding_error_handler,
        )

        async with stdio_client(stdio_params) as (read, write):
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
            # Create StdioServerParameters object from config
            stdio_params = StdioServerParameters(
                command=self.config.command,
                args=self.config.args,
                env=self.config.env,
                cwd=self.config.cwd,
                encoding=self.config.encoding,
                encoding_error_handler=self.config.encoding_error_handler,
            )

            async with stdio_client(stdio_params) as (read, write):
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
