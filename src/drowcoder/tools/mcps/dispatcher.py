import json
import pathlib
import yaml
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from streamable_http import MCPStreamableHTTPClient


DEFAULT_SOURCE_FILE = pathlib.Path(__file__).resolve().parent / 'mcps.json'

@dataclass(frozen=True)
class MCPTransportType:
    STREAMABLE_HTTP : str = 'streamable_http'
    STDIO           : str = 'stdio'
    INVALID         : str = 'invalid'

@dataclass
class MCPInstance:
    name           : str
    config         : Dict[str, Any]
    client         : Optional[MCPStreamableHTTPClient] = None
    tool_descs     : Optional[List[dict]] = None
    transport_type : Optional[str] = None

    def __post_init__(self):
        if self.client is None: self.update_client()

    def update_client(self, config: Optional[Dict[str, Any]] = None):

        if config:
            self.config = config

        has_url = 'url' in self.config
        has_command = 'command' in self.config

        if has_url and has_command:
            # TODO: emit warning instead of raising error once logging is supported in upcoming version
            raise ValueError(f"Server '{self.name}' has both 'url' and 'command' fields, skip to init '{self.name}' client")
        elif has_url:
            self.transport_type = MCPTransportType.STREAMABLE_HTTP
            self.client = MCPStreamableHTTPClient(**self.config)
            self.tool_descs = self.client.tool_descs
            # TODO: handle client registration status (success or failed)
        elif has_command:
            self.transport_type = MCPTransportType.STDIO
            # TODO: support stdio client in upcoming version
            pass
        else:
            self.transport_type = MCPTransportType.INVALID
            # TODO: handle invalid mcp config in upcoming version
            pass

class MCPDispatcherSourceLoader:

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
            return source.get('mcpServers', {})

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
            return source.get('mcpServers', {})

class MCPDispatcher(MCPDispatcherSourceLoader):

    def __init__(self, source_file: Union[None, str, pathlib.Path] = None):
        """
        Initialize MCP dispatcher with configuration file.

        Args:
            source_file: Path to configuration file. Defaults to './mcps.json' if None.
        """
        if not source_file:
            source_file = DEFAULT_SOURCE_FILE

        mcps = self.load(source_file)

        # Use deepcopy to ensure default_mcps and active_mcps are independent
        mcps = {
            server_name: MCPInstance(name=server_name, config=config)
            for server_name, config in mcps.items()
        }
        self.default_mcps = deepcopy(mcps)
        self.mcps = deepcopy(mcps)

    def apply_mcps(self, source_file: Union[None, str, pathlib.Path] = None) -> None:
        """
        Apply additional MCP configuration from file, merging with existing mcps.

        Args:
            source_file: Path to configuration file. If None, does nothing.
        """
        if not source_file:
            return

        mcps = self.load(source_file)
        for server_name, config in mcps.items():

            try:
                if server_name in self.mcps:
                    self.mcps[server_name].update_client(config)
                else:
                    self.mcps[server_name] = MCPInstance(name=server_name, config=config)
            except:
                # TODO: emit warning instead of raising error once logging is supported in upcoming version
                raise
