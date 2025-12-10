import sys
import json
import yaml
import pathlib
import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Callable, Optional, Union
from copy import deepcopy

from .base import BaseTool
from .load import LoadTool as load
from .search import SearchTool as search
from .search_and_replace import SearchAndReplaceTool as search_and_replace
from .attempt_completion import AttemptCompletionTool as attempt_completion
from .write import WriteTool as write
from .bash import BashTool as bash
from .todo import TodoTool as update_todos


DEFAULT_TOOL_CONFIG_ROOT = pathlib.Path(__file__).resolve().parent
DEFAULT_TOOL_CONFIGS = [
    'attempt_completion.yaml',
    'bash.yaml',
    'load.yaml',
    'search_and_replace.yaml',
    'search.yaml',
    'write.yaml',
    'todo.yaml',
]

@dataclass
class OpenAICompatibleFuncDesc:
    name: str
    description: str
    parameters: Dict[str, Any]
    strict: bool = False

@dataclass
class ToolInstance:
    """Configuration for a single tool"""
    name: str
    desc: Dict[str, OpenAICompatibleFuncDesc]  # OpenAI tool description
    func: Callable
    enabled: bool = True
    registered: bool = False

@dataclass
class ToolDispatcherConfig:
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
            self.paths = DEFAULT_TOOL_CONFIGS
            self.root = DEFAULT_TOOL_CONFIG_ROOT
        elif not self.paths:
            # Case 2: Custom root with default paths
            self.paths = DEFAULT_TOOL_CONFIGS
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

class ToolDispatcherConfigLoader:

    tag = 'tools'

    def load(self, source_file: Union[None, str, pathlib.Path] = None) -> List[Any]:
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

    def load_from_yaml(self, source_file: pathlib.Path) -> List[Any]:
        """
        Load configuration from YAML file.

        Args:
            source_file: Path to YAML file

        Returns:
            Dictionary containing toolServers configuration, or empty dict if not found
        """
        with open(source_file, 'r', encoding='utf-8') as f:
            source = yaml.safe_load(f) or {}
            return source.get(self.tag, [])

    def load_from_json(self, source_file: pathlib.Path) -> List[Any]:
        """
        Load configuration from JSON file.

        Args:
            source_file: Path to JSON file

        Returns:
            Dictionary containing toolServers configuration, or empty dict if not found
        """
        with open(source_file, 'r', encoding='utf-8') as f:
            source = json.load(f) or {}
            return source.get(self.tag, [])

class ToolDispatcher(ToolDispatcherConfigLoader):

    def __init__(
        self,
        config_paths: Union[None, str, pathlib.Path, List[Union[str, pathlib.Path]]] = None,
        config_root: Union[None, str, pathlib.Path] = None,
        logger: Optional[logging.Logger] = None,
        callback: Optional[Callable] = None,
        checkpoint: Optional[Union[str, pathlib.Path]] = None,
    ):
        self.logger = logger
        self.callback = callback
        self.checkpoint = checkpoint

        self.current_module = sys.modules[__name__]

        self.default_tools :Dict[str, ToolInstance] = {}
        self.tools         :Dict[str, ToolInstance] = {}

        # Store initial configuration for later reloading
        self._init_config_paths = config_paths
        self._init_config_root = config_root

        self.apply_tools(config_paths, config_root=config_root)
        self.default_tools = deepcopy(self.tools)

    def apply_tools(
        self,
        config_paths: Union[None, str, pathlib.Path, List[Union[str, pathlib.Path]]] = None,
        config_root: Union[None, str, pathlib.Path] = None,
    ) -> Dict[str, ToolInstance]:
        """
        Load and apply tool instances from configuration file(s).

        If a tool already exists, it will be updated.
        If a tool doesn't exist, creates a new ToolInstance.

        Args:
            config_paths: Path(s) to configuration file(s). If None, uses initial configuration.
            config_root: Root directory for resolving paths. If None, uses initial root.

        Returns:
            Dictionary mapping tool names to ToolInstance objects.

        Behavior:
            - apply_tools(): Reload from initial configuration
            - apply_tools("new.yaml"): Load from new configuration
            - apply_tools("new.yaml", "/new/root"): Load with new root
        """
        # If no arguments provided, use initial configuration
        if config_paths is None and config_root is None:
            config_paths = self._init_config_paths
            config_root = self._init_config_root

        tool_config = ToolDispatcherConfig(paths=config_paths, root=config_root)

        for config_path in tool_config.paths:
            tool_configs = self.load(config_path)  # Returns List[dict]

            # Iterate through tool configurations
            for config in tool_configs:
                tool_instance = self.setup_tool(config)
                if tool_instance:
                    self.tools[tool_instance.name] = tool_instance

        return self.tools

    def setup_tool(self, config: Dict[str, Any]) -> Optional[ToolInstance]:
        """
        Setup a single tool instance from configuration.

        Args:
            config: Tool configuration dictionary containing 'type' and function details.

        Returns:
            ToolInstance if successfully configured, None otherwise.
        """
        tool_type = config.get('type')
        if tool_type != 'function':
            # TODO: Short-term handling - only support 'function' type currently
            if self.logger:
                self.logger.warning(
                    f"Unsupported tool type '{tool_type}'. Only 'function' type is supported currently."
                )
            return None

        func_desc = config[tool_type]
        func_name = func_desc['name']

        if func_name in self.current_module.__dict__:
            func = self.current_module.__dict__[func_name]

            if isinstance(func, type) and issubclass(func, BaseTool):
                func = func(
                    logger=self.logger,
                    callback=self.callback,
                    checkpoint=self.checkpoint,
                )
                func = func.execute
                registered = True
            else:
                if self.logger:
                    self.logger.warning(f"Function {func_name} is not a BaseTool subclass")
                func = None
                registered = False
        else:
            if self.logger:
                self.logger.warning(f"Function {func_name} not found in module")
            func = None
            registered = False

        tool_instance = ToolInstance(
            name=func_name,
            desc=func_desc,
            func=func,
            registered=registered,
        )
        return tool_instance
