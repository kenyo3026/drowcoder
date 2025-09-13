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


def setup_config(yaml_path: Union[str, pathlib.Path]):
    yaml_path = pathlib.Path(yaml_path)

    # Ensure file exists
    if not yaml_path.exists():
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_path.touch()

    # Read existing config
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}

    # Check if config is valid
    models = config.get('models', [])
    if (isinstance(config, dict) and models and
        isinstance(models, list) and len(models) > 0):
        first_model = models[0]
        if first_model.get('model') and first_model.get('api_key'):
            return yaml_path.__str__()

    # Config is invalid, prompt for new values
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

    return yaml_path.__str__()

@dataclass
class CliArgs(MainArgs):
    config          :str = str(pathlib.Path.home() / '.drowcoder' / 'config.yaml')
    model           :str = None
    workspace       :str = None
    checkpoint      :str = None
    checkpoint_root :str = str(pathlib.Path.home() / '.drowcoder' / 'checkpoints')

    def __post_init__(self):
        self.config = setup_config(self.config)
        super().__post_init__()

class CliMain(Main):
    args:Type[CliArgs] = CliArgs


if __name__ == "__main__":
    sys.exit(CliMain.run())
