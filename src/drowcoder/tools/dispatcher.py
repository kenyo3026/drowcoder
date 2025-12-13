import sys
import json
import yaml
import pathlib
import logging
from dataclasses import asdict, dataclass
from typing import Dict, List, Any, Callable, Optional, Union
from copy import deepcopy

from .mcps.dispatcher import MCPDispatcher
from .tools.dispatcher import ToolDispatcher


class Dispatcher:

    def __init__(
        self,
        tool_configs: Union[
            None,
            str,
            pathlib.Path,
            List[Union[str, pathlib.Path]],
            List[Dict[str, Any]]
        ] = None,
        mcp_configs: Union[
            None,
            str,
            pathlib.Path,
            List[Union[str, pathlib.Path]],
            Dict[str, Any],
        ] = None,
        logger: Optional[logging.Logger] = None,
        callback: Optional[Callable] = None,
        checkpoint: Optional[Union[str, pathlib.Path]] = None,
    ):
        self.tool_configs = tool_configs
        self.mcp_configs = mcp_configs

        self.logger = logger or logging.getLogger(__name__)
        self.callback = callback
        self.checkpoint = checkpoint

        self.tool_dispatcher = ToolDispatcher(
            self.tool_configs,
            logger = logger,
            callback = callback,
            checkpoint = checkpoint,
        )
        self.mcp_dispatcher = MCPDispatcher(
            self.mcp_configs,
            logger = logger,
            callback = callback,
            checkpoint = checkpoint,
        )

    def apply_tools(self, *args, **kwargs):
        return self.tool_dispatcher.apply_tools(*args, **kwargs)

    def apply_mcps(self, *args, **kwargs):
        return self.mcp_dispatcher.apply_mcps(*args, **kwargs)

    def expose_descs(self) -> List[Dict[str, Any]]:
        """Get all tool descriptions (tools + MCP servers)"""
        tool_descs = self.expose_tool_descs()
        mcp_descs = self.expose_mcp_descs()

        # Validate MCP tool descriptions format
        for desc in mcp_descs:
            if not isinstance(desc, dict):
                self.logger.warning(f"Invalid MCP tool description format: {desc}")
                continue
            if 'type' not in desc or desc.get('type') != 'function':
                self.logger.warning(f"MCP tool description missing 'type': {desc}")
            if 'function' not in desc:
                self.logger.warning(f"MCP tool description missing 'function': {desc}")

        return tool_descs + mcp_descs

    def expose_tool_descs(self) -> List[Dict[str, Any]]:
        """Get tool descriptions from tool dispatcher"""
        return self.tool_dispatcher.get_tool_descs()

    def expose_mcp_descs(self) -> List[Dict[str, Any]]:
        """Get tool descriptions from MCP dispatcher"""
        return self.mcp_dispatcher.get_mcp_descs()

    def expose_funcs(self) -> Dict[str, Callable]:
        """Get all tool functions (tools + MCP servers) merged into a single dict"""
        tool_funcs = self.expose_tool_funcs()
        mcp_funcs = self.expose_mcp_funcs()

        # Check for name conflicts
        conflicts = set(tool_funcs.keys()) & set(mcp_funcs.keys())
        if conflicts:
            self.logger.warning(
                f"Tool name conflicts detected: {conflicts}. "
                f"MCP tools will override builtin tools with the same name."
            )

        return {**tool_funcs, **mcp_funcs}

    def expose_tool_funcs(self) -> Dict[str, Callable]:
        """Get tool functions from tool dispatcher"""
        return self.tool_dispatcher.get_tool_funcs()

    def expose_mcp_funcs(self) -> Dict[str, Callable]:
        """Get tool functions from MCP dispatcher"""
        return self.mcp_dispatcher.get_mcp_funcs()