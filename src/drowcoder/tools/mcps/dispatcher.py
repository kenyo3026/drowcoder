import json
import logging
import pathlib
import yaml
from copy import deepcopy
from dataclasses import dataclass
from functools import partial
from typing import Any, Dict, List, Callable, Optional, Union

from .stdio import MCPStdioClient
from .streamable_http import MCPStreamableHTTPClient


DEFAULT_MCP_CONFIG_ROOT = pathlib.Path(__file__).resolve().parent
DEFAULT_MCP_CONFIG = 'mcps.json'

@dataclass(frozen=True)
class MCPTransportType:
    STREAMABLE_HTTP : str = 'streamable_http'
    STDIO           : str = 'stdio'
    INVALID         : str = 'invalid'

@dataclass
class MCPInstance:
    name           : str
    config         : Dict[str, Any]
    client         : Optional[Union[MCPStreamableHTTPClient, MCPStdioClient]] = None
    descs          : Optional[List[dict]] = None
    transport_type : Optional[str] = None
    enabled        : bool = True
    registered     : bool = False

    def __post_init__(self):
        if self.client is None: self.update_client()

    def update_client(self, config: Optional[Dict[str, Any]] = None):

        if config:
            self.config = config

        if self.config is None:
            self.config = {}

        has_url = 'url' in self.config
        has_command = 'command' in self.config

        if has_url and has_command:
            # TODO: emit warning instead of raising error once logging is supported in upcoming version
            raise ValueError(f"Server '{self.name}' has both 'url' and 'command' fields, skip to init '{self.name}' client")
        elif has_url:
            self.transport_type = MCPTransportType.STREAMABLE_HTTP
            self.client = MCPStreamableHTTPClient(**self.config)
            self.descs = self.client.tool_descs
        elif has_command:
            self.transport_type = MCPTransportType.STDIO
            self.client = MCPStdioClient(**self.config)
            self.descs = self.client.tool_descs
        else:
            self.transport_type = MCPTransportType.INVALID
            self.client = None
            self.descs = None

@dataclass
class MCPDispatcherConfig:
    """Configuration for MCP dispatcher paths and root directory."""
    paths: Union[None, str, pathlib.Path, List[Union[str, pathlib.Path]]] = None
    root: Union[None, str, pathlib.Path] = None

    def __post_init__(self):
        """Normalize configuration paths with optional root directory."""
        # Handle config paths and root with fallback logic:
        # 1. Both None: use defaults
        # 2. Only root given: use default paths with custom root
        # 3. Only paths given: normalize paths, set root to None
        if not self.paths and not self.root:
            # Case 1: Use all defaults
            self.paths = DEFAULT_MCP_CONFIG
            self.root = DEFAULT_MCP_CONFIG_ROOT
        elif not self.paths:
            # Case 2: Custom root with default paths
            self.paths = DEFAULT_MCP_CONFIG
        elif not self.root:
            # Case 3: Custom paths, no root
            self.root = None

        # Normalize to list
        if isinstance(self.paths, (str, pathlib.Path)):
            self.paths = [self.paths]

        # Apply root to paths
        if self.root:
            self.root = pathlib.Path(self.root)
            self.paths = [self.root / path for path in self.paths]

class MCPDispatcherConfigLoader:

    tag = 'mcpServers'

    def load(self, source_file: Union[None, str, pathlib.Path] = None) -> Dict[str, Any]:
        """
        Load configuration from YAML or JSON file.

        Args:
            source_file: Path to configuration file (.yaml, .yml, or .json)

        Returns:
            Dictionary containing loaded configuration, or empty dict if source_file is None

        Raises:
            ValueError: If file extension is not supported
            FileNotFoundError: If file does not exist
            yaml.YAMLError: If YAML file is invalid
            json.JSONDecodeError: If JSON file is invalid
        """
        if not source_file:
            return {}

        if isinstance(source_file, str):
            source_file = pathlib.Path(source_file).resolve()

        if not source_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {source_file}")

        if source_file.suffix in {".yaml", ".yml"}:
            return self.load_from_yaml(source_file)

        elif source_file.suffix == ".json":
            return self.load_from_json(source_file)

        else:
            raise ValueError(
                f"Unsupported file extension: {source_file.suffix}. "
                f"Supported extensions: .yaml, .yml, .json"
            )

    def load_from_yaml(self, source_file: pathlib.Path) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Args:
            source_file: Path to YAML file

        Returns:
            Dictionary containing mcpServers configuration, or empty dict if not found
        """
        with open(source_file, 'r', encoding='utf-8') as f:
            source = yaml.safe_load(f) or {}
            return source.get(self.tag, {})

    def load_from_json(self, source_file: pathlib.Path) -> Dict[str, Any]:
        """
        Load configuration from JSON file.

        Args:
            source_file: Path to JSON file

        Returns:
            Dictionary containing mcpServers configuration, or empty dict if not found
        """
        with open(source_file, 'r', encoding='utf-8') as f:
            source = json.load(f) or {}
            return source.get(self.tag, {})

class MCPDispatcher(MCPDispatcherConfigLoader):

    def __init__(
        self,
        configs: Union[None, str, pathlib.Path, List[Union[str, pathlib.Path]], Dict[str, Any]] = None,
        config_root: Union[None, str, pathlib.Path] = None,
        logger: Optional[logging.Logger] = None,
        callback: Optional[Callable] = None,
        checkpoint: Optional[Union[str, pathlib.Path]] = None,
    ):
        """
        Initialize MCP dispatcher with configuration file.

        Args:
            configs: Path(s) to configuration file(s). Defaults to 'mcps.json' if None.
            config_root: Root directory for resolving config paths. Defaults to module directory if None.
        """
        self.logger = logger or logging.getLogger(__name__)
        self.callback = callback
        self.checkpoint = checkpoint

        self.default_mcps :Dict[str, MCPInstance] = {}
        self.mcps         :Dict[str, MCPInstance] = {}

        # Store initial configuration for later reloading
        self._init_configs = configs
        self._init_config_root = config_root

        self.apply_mcps(configs, config_root=config_root)
        self.default_mcps = deepcopy(self.mcps)

    def apply_mcps(
        self,
        configs: Union[None, str, pathlib.Path, List[Union[str, pathlib.Path]], Dict[str, Any]] = None,
        config_root: Union[None, str, pathlib.Path] = None,
    ) -> Dict[str, MCPInstance]:
        """
        Load and apply MCP instances from configuration file or direct config dict.

        If a server already exists, updates its configuration and client.
        If a server doesn't exist, creates a new MCPInstance.

        Args:
            configs: Configuration source. Can be:
                - None: Uses initial configuration
                - str/Path: Single configuration file path
                - List[str/Path]: Multiple configuration file paths
                - Dict[str, Any]: Direct MCP servers configuration
                    Format: {"server_name": {"url": "...", "headers": {...}}, ...}
                    OR: {"mcpServers": {"server_name": {...}, ...}}
            config_root: Root directory for resolving relative paths.
                If None, uses initial root.

        Returns:
            Dictionary mapping server names to MCPInstance objects.

        Behavior:
            - apply_mcps(): Reload from initial configuration
            - apply_mcps("new.json"): Load from new configuration file
            - apply_mcps("new.json", "/new/root"): Load with custom root
            - apply_mcps({"server_name": {...}}): Apply direct configuration dict
        """
        # If no arguments provided, use initial configuration
        if configs is None and config_root is None:
            configs = self._init_configs
            config_root = self._init_config_root

        # Handle Dict case - direct MCP servers configuration
        if isinstance(configs, dict):
            # Extract mcpServers if present, otherwise assume configs is mcpServers dict
            configs = configs.get(self.tag, configs)
        else:
            # Handle file paths case
            mcp_config = MCPDispatcherConfig(paths=configs, root=config_root)

            configs = {}
            for config_path in mcp_config.paths:
                _configs = self.load(config_path)

                for server_name in _configs:
                    if self.logger:
                        _configs[server_name]['logger'] = self.logger
                    if self.checkpoint:
                        _configs[server_name]['checkpoint'] = self.checkpoint
                    if self.callback:
                        _configs[server_name]['callback'] = self.callback

                    configs.update(_configs)

        for server_name, config in configs.items():
            if server_name in self.mcps:
                # Update existing instance (preserves object reference)
                self.mcps[server_name].update_client(config)
            else:
                # Create new instance
                self.mcps[server_name] = MCPInstance(name=server_name, config=config)

        return self.mcps

    def disable_mcps(self, mcp_names: List[str]):
        """Disable specific MCP servers by name"""
        for mcp_name in mcp_names:
            if mcp_name in self.mcps:
                self.mcps[mcp_name].enabled = False

    def enable_mcps(self, mcp_names: List[str]):
        """Enable specific MCP servers by name"""
        for mcp_name in mcp_names:
            if mcp_name in self.mcps:
                self.mcps[mcp_name].enabled = True

    def get_mcp_descs(self) -> List[Dict[str, Any]]:
        """Get OpenAI tool descriptions of all enabled MCP servers"""
        return [
            desc
            for instance in self.mcps.values() if instance.enabled
            for desc in (instance.descs or [])
        ]

    def get_mcp_funcs(self) -> Dict[str, Callable]:
        """Get tool functions from all enabled MCP servers"""
        return {
            desc['function']['name']: partial(
                self.mcps[name].client.call_tool, tool_name=desc['function']['name']
            )
            for name, instance in self.mcps.items() if instance.enabled
            for desc in (instance.descs or [])
        }

    def get_mcp_clients(self) -> Dict[str, Callable]:
        """Get functions of all enabled tools"""
        # return {name: instance.tool for name, instance in self.tools.items() if instance.enabled}
        return {
            name:instance.client for name, instance in self.mcps.items()
            if instance.enabled
        }