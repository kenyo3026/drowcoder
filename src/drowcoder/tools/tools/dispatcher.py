import sys
import json
import yaml
import pathlib
import logging
from dataclasses import asdict, dataclass
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
    """
    Configuration for a single tool instance.

    Attributes:
        name: Tool identifier/name
        desc: Complete tool description dictionary in OpenAI format
        tool: Tool executor (Callable for 'function' type, may differ for other types)
        type: Tool type ('function', 'websearch', etc.)
        enabled: Whether the tool is enabled
        registered: Whether the tool was successfully registered
    """
    name: str
    desc: Dict[str, Any]
    tool: Callable
    type: str
    enabled: bool = True
    registered: bool = False

@dataclass
class ToolDispatcherConfig:
    """Configuration for tool dispatcher paths and root directory."""
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
        Load tool configurations from YAML or JSON file.

        Args:
            source_file: Path to configuration file (.yaml, .yml, or .json)

        Returns:
            List of tool configurations from the 'tools' key in the file.
            Returns empty list if source_file is None or 'tools' key not found.

        Raises:
            ValueError: If file extension is not supported
            FileNotFoundError: If file does not exist
            yaml.YAMLError: If YAML file is invalid
            json.JSONDecodeError: If JSON file is invalid
        """
        if not source_file:
            return []

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
        Load tool configurations from YAML file.

        Args:
            source_file: Path to YAML file

        Returns:
            List of tool configurations from the 'tools' key, or empty list if not found
        """
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                source = yaml.safe_load(f) or {}
                return source.get(self.tag, [])
        except (yaml.YAMLError, ValueError):
            # Handle empty or invalid YAML files
            return []

    def load_from_json(self, source_file: pathlib.Path) -> List[Any]:
        """
        Load tool configurations from JSON file.

        Args:
            source_file: Path to JSON file

        Returns:
            List of tool configurations from the 'tools' key, or empty list if not found
        """
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                source = json.load(f) or {}
                return source.get(self.tag, [])
        except (json.JSONDecodeError, ValueError):
            # Handle empty or invalid JSON files
            return []

class ToolDispatcher(ToolDispatcherConfigLoader):
    """
    Tool dispatcher for loading and managing tool instances.

    Supports loading tools from configuration files (YAML/JSON) or direct tool
    configurations. Automatically loads default builtin tools when initialized
    without configs parameter.

    Currently supports 'function' type tools. Designed to support additional
    tool types (e.g., 'websearch') in the future.
    """

    def __init__(
        self,
        configs: Union[None, str, pathlib.Path, List[Union[str, pathlib.Path]], List[Dict[str, Any]]] = None,
        config_root: Union[None, str, pathlib.Path] = None,
        logger: Optional[logging.Logger] = None,
        callback: Optional[Callable] = None,
        checkpoint: Optional[Union[str, pathlib.Path]] = None,
    ):
        """
        Initialize tool dispatcher with configuration.

        Args:
            configs: Tool configuration source. Can be:
                - None: Load default builtin tools (DEFAULT_TOOL_CONFIGS)
                - str/Path: Single configuration file path
                - List[str/Path]: Multiple configuration file paths
                - List[Dict]: Direct tool configurations in OpenAI format
            config_root: Root directory for resolving relative config paths.
                If None, uses DEFAULT_TOOL_CONFIG_ROOT.
            logger: Optional logger instance
            callback: Optional callback function
            checkpoint: Optional checkpoint directory

        Behavior:
            - If configs=None: Automatically loads all default builtin tools
            - If configs=List[Dict]: Directly applies tool configurations
            - If configs=file path(s): Loads tools from configuration files
        """
        self.logger = logger or logging.getLogger(__name__)
        self.callback = callback
        self.checkpoint = checkpoint

        self.current_module = sys.modules[__name__]

        self.default_tools :Dict[str, ToolInstance] = {}
        self.tools         :Dict[str, ToolInstance] = {}

        # Store initial configuration for later reloading
        self._init_configs = configs
        self._init_config_root = config_root

        # Load system config as default, then apply user config if provided
        self.apply_tools()
        if configs:
            self.apply_tools(configs, config_root=config_root)

        self.default_tools = deepcopy(self.tools)

    def apply_tools(
        self,
        configs: Union[None, str, pathlib.Path, List[Union[str, pathlib.Path]], List[Dict[str, Any]]] = None,
        config_root: Union[None, str, pathlib.Path] = None,
    ) -> Dict[str, ToolInstance]:
        """
        Load and apply tool instances from configuration source.

        If a tool already exists (same name), it will be updated.
        If a tool doesn't exist, creates a new ToolInstance.

        Args:
            configs: Tool configuration source. Can be:
                - None: Uses initial configuration
                - str/Path: Single configuration file path
                - List[str/Path]: Multiple configuration file paths
                - List[Dict]: Direct tool configurations in OpenAI format
                    Format: [{"type": "function", "function": {...}}, ...]
            config_root: Root directory for resolving relative paths.
                If None, uses initial root.

        Returns:
            Dictionary mapping tool names to ToolInstance objects.

        Behavior:
            - apply_tools(): Reload from initial configuration
            - apply_tools("new.yaml"): Load from new configuration file
            - apply_tools("new.yaml", "/new/root"): Load with custom root
            - apply_tools([{...}, {...}]): Apply direct tool configurations
        """
        # If no arguments provided, use initial configuration
        if configs is None and config_root is None:
            configs = self._init_configs
            config_root = self._init_config_root

        # Handle List[Dict] case - direct tool configs
        if isinstance(configs, list) and configs and isinstance(configs[0], dict):
            # Direct tool configurations (from agent.py tools parameter)
            for config in configs:
                tool_instance = self.setup_tool(config)
                if tool_instance:
                    self.tools[tool_instance.name] = tool_instance
        else:
            # Handle file paths case
            tool_config = ToolDispatcherConfig(paths=configs, root=config_root)

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

        Validates and processes tool configuration, instantiates the tool executor,
        and creates a ToolInstance with validated description.

        Args:
            config: Tool configuration dictionary in OpenAI format.
                Must contain 'type' key (currently only 'function' supported).
                Future support for 'websearch' and other types planned.

        Returns:
            ToolInstance if successfully configured, None otherwise.

        Raises:
            ValueError: If tool type is not supported.

        Note:
            The desc field contains the complete validated config. For 'function'
            type, function description is validated through OpenAICompatibleFuncDesc.
        """
        tool_type = config.get('type')

        if tool_type == 'function':

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

            tool_desc = config
            tool_desc.update(asdict(OpenAICompatibleFuncDesc(**func_desc)))

            tool_instance = ToolInstance(
                name=func_name,
                desc=tool_desc,
                tool=func,
                type=tool_type,
                registered=registered,
            )
        else:
            # TODO: Short-term handling - only support 'function' type currently
            msg = f"Unsupported tool type '{tool_type}'. Only 'function' type is supported currently."
            if self.logger:
                self.logger.error(msg)
            raise ValueError(msg)

        return tool_instance

    def disable_tools(self, tool_names: List[str]):
        """Disable specific tools by name"""
        for tool_name in tool_names:
            if tool_name in self.tools:
                self.tools[tool_name].enabled = False

    def enable_tools(self, tool_names: List[str]):
        """Enable specific tools by name"""
        for tool_name in tool_names:
            if tool_name in self.tools:
                self.tools[tool_name].enabled = True

    def get_tool_descs(self) -> List[Dict[str, Any]]:
        """Get OpenAI tool descriptions of all enabled tools"""
        return [instance.desc for instance in self.tools.values() if instance.enabled]

    def get_tool_funcs(self) -> Dict[str, Callable]:
        """Get functions of all enabled tools"""
        return {name: instance.tool for name, instance in self.tools.items() if instance.enabled}
