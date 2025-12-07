import logging
import asyncio
from dataclasses import dataclass, field, asdict
from functools import wraps
from typing import Dict, Callable, Optional, Union, Any, List
from pathlib import Path

import mcp
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from base import MCPBaseClient
from utils import OpenAICompatibleDesc


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
        auto_load: bool = True,
        **kwargs,
    ):
        # Initialize parent class (logger, callback, checkpoint)
        super().__init__(
            logger=logger,
            callback=callback,
            checkpoint=checkpoint,
        )
        # Initialize Streamable HTTP specific config
        self.config = MCPStreamableHTTPClientConfig(
            url=url,
            headers=headers or {},
        )

        # Load tool descriptions synchronously on init
        if auto_load:
            loop = asyncio.get_event_loop()
            self.tool_descs = loop.run_until_complete(
                self.list_tools(dump_to_openai_desc=True)
            )
        else:
            self.tool_descs: Optional[List[Dict[str, Any]]] = None

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

    async def list_tools(self, dump_to_openai_desc: bool = False):
        """List all available tools from the MCP server"""
        async with streamablehttp_client(**asdict(self.config)) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()

                if dump_to_openai_desc:
                    return [
                        asdict(OpenAICompatibleDesc.from_mcp_type_tool(tool))
                        for tool in tools_response.tools
                    ]
                return tools_response.tools

    async def call_tool(self, tool_name: str, arguments: Dict):
        """Call a specific tool with given arguments"""
        async with streamablehttp_client(**asdict(self.config)) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result