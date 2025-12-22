"""
CLI Entry Point for drowcoder (Production Environment)

This module provides the CLI entry point for the installed drowcoder package.
It uses the standard user directory (~/.drowcoder/checkpoints/) for storing checkpoints.
"""

import pathlib
import sys
import yaml
from dataclasses import dataclass
from typing import Union, Type

from .main import Main, MainArgs


def setup_config(yaml_paths: Union[str, pathlib.Path, list, None]):
    """
    Setup configuration for CLI mode.

    Priority:
    1. -c parameter (yaml_paths) → return as-is for ConfigMorpher
    2. System default (~/.drowcoder/config.yaml) with first-time setup

    Returns:
        Config path(s) for ConfigMorpher (str, Path, or list)
    """
    # If user provided -c, use it directly (supports multi-config merging)
    if yaml_paths:
        return yaml_paths

    # Use system default (~/.drowcoder/config.yaml)
    default_config = pathlib.Path.home() / '.drowcoder' / 'config.yaml'

    # If system default doesn't exist, create it
    if not default_config.exists():
        return _create_default_config(default_config)

    return str(default_config)

def _create_default_config(yaml_path: pathlib.Path) -> str:
    """
    Create a new configuration file with user input.

    Args:
        yaml_path: Path where the config file should be created

    Returns:
        String path to the created config file
    """
    # Ensure directory exists
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    # Prompt for model and API key
    print(f"\n🔧 Setting up configuration at: {yaml_path}")
    print("=" * 60)

    while True:
        model = input('Input a 🧠 model (should be litellm): ').strip()
        if model:
            break

    while True:
        api_key = input('Input a 🔑 api key (should be litellm): ').strip()
        if api_key:
            break

    # Create new config
    config = {
        'models': [{
            'name': model,
            'model': model,
            'api_key': api_key,
        }]
    }

    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    print(f"✅ Configuration saved to: {yaml_path}\n")

    return str(yaml_path)

@dataclass
class CliArgs(MainArgs):
    config          :Union[str, list] = None  # Will be set to default in __post_init__
    model           :str = None
    workspace       :str = None
    checkpoint      :str = None
    checkpoint_root :str = str(pathlib.Path.home() / '.drowcoder' / 'checkpoints')

    def __post_init__(self):
        self.config = setup_config(self.config)
        super().__post_init__()

class CliMain(Main):
    args:Type[CliArgs] = CliArgs


def main() -> int:
    """CLI entry point function for setuptools console_scripts."""
    return CliMain.run()


if __name__ == "__main__":
    sys.exit(main())
