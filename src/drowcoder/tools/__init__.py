import os
import sys
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Callable
from copy import deepcopy

from .load import *
from .search import *
from .search_and_replace import *
from .attempt_completion import *
from .write import *
from .execute import *
from .todo import *


@dataclass
class ToolConfig:
    """Configuration for a single tool"""
    name: str
    description: Dict[str, Any]  # Complete OpenAI tool description
    function: Callable
    enabled: bool = True

    @classmethod
    def from_desc(cls, desc: Dict[str, Any], func: Callable):
        return cls(
            name=desc['function']['name'],
            description=desc,
            function=func
        )


class ToolManager:
    """Tool manager - handles loading, managing and configuring tools"""

    def __init__(self, tool_root: Optional[Path] = None):
        self.tool_root = tool_root or Path(__file__).parent
        self.builtin_yamls = [
            'attempt_completion.yaml',
            'execute.yaml',
            'load.yaml',
            'search_and_replace.yaml',
            'search.yaml',
            'write.yaml',
            'todo.yaml',
        ]

        # Store all tool configurations
        self._builtin_tools: Dict[str, ToolConfig] = {}
        self._active_tools: Dict[str, ToolConfig] = {}

        # Load builtin tools
        self._load_builtin_tools()

        # Default to use all builtin tools
        self._active_tools.update(deepcopy(self._builtin_tools))

    def _load_builtin_tools(self):
        """Load all builtin tools from YAML files"""
        current_module = sys.modules[__name__]

        for yaml_file in self.builtin_yamls:
            yaml_path = os.path.join(self.tool_root, yaml_file)
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                # Each YAML contains tools list with OpenAI format
                tool_descs = config.get('tools', [])
                for desc in tool_descs:
                    func_name = desc['function']['name']

                    # Ensure function exists in module
                    if func_name in current_module.__dict__:
                        func = current_module.__dict__[func_name]
                        tool_config = ToolConfig.from_desc(desc, func)
                        self._builtin_tools[func_name] = tool_config
                    else:
                        print(f"Warning: Function {func_name} not found in module")

            except (FileNotFoundError, yaml.YAMLError, KeyError) as e:
                print(f"Warning: Failed to load {yaml_file}: {e}")

    def apply_config_tools(self, config_tools: Optional[List[Dict[str, Any]]] = None):
        """
        Apply config.yaml tools list to override/extend builtin tools

        config_tools format: List of OpenAI tool descriptions
        [
            {
                "type": "function",
                "function": {
                    "name": "load",
                    "description": "Custom description",
                    "parameters": {...}
                }
            }
        ]
        """
        if not config_tools:
            return

        current_module = sys.modules[__name__]

        for tool_desc in config_tools:
            # Validate OpenAI tool description format
            if not self._is_valid_openai_tool_desc(tool_desc):
                raise ValueError(f"Invalid OpenAI tool description format: {tool_desc}")

            func_name = tool_desc['function']['name']

            # Only allow tools that have corresponding functions in this module
            if func_name not in current_module.__dict__:
                raise ValueError(f"Function {func_name} not found in tools module")

            # Create or override tool configuration
            func = current_module.__dict__[func_name]
            tool_config = ToolConfig.from_desc(tool_desc, func)
            self._active_tools[func_name] = tool_config

    def _is_valid_openai_tool_desc(self, desc: Dict[str, Any]) -> bool:
        """Validate OpenAI tool description format"""
        try:
            return (
                desc.get('type') == 'function' and
                'function' in desc and
                'name' in desc['function'] and
                'description' in desc['function']
            )
        except (TypeError, AttributeError):
            return False

    def disable_tools(self, tool_names: List[str]):
        """Disable specific tools by name"""
        for tool_name in tool_names:
            if tool_name in self._active_tools:
                self._active_tools[tool_name].enabled = False

    def enable_tools(self, tool_names: List[str]):
        """Enable specific tools by name"""
        for tool_name in tool_names:
            if tool_name in self._builtin_tools:
                tool_config = deepcopy(self._builtin_tools[tool_name])
                tool_config.enabled = True
                self._active_tools[tool_name] = tool_config

    def get_tool_descs(self) -> List[Dict[str, Any]]:
        """Get OpenAI tool descriptions of all enabled tools"""
        return [tool.description for tool in self._active_tools.values() if tool.enabled]

    def get_tool_funcs(self) -> Dict[str, Callable]:
        """Get functions of all enabled tools"""
        return {name: tool.function for name, tool in self._active_tools.items() if tool.enabled}

    def list_available_tools(self) -> List[str]:
        """List all available builtin tool names"""
        return list(self._builtin_tools.keys())

    def list_active_tools(self) -> List[str]:
        """List all enabled tool names"""
        return [name for name, tool in self._active_tools.items() if tool.enabled]

    def get_tool_info(self, tool_name: str) -> Optional[ToolConfig]:
        """Get detailed information of a specific tool"""
        return self._active_tools.get(tool_name)


# Create global tool manager instance
tool_manager = ToolManager()

