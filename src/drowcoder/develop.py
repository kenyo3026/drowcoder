"""
Development Entry Point for drowcoder

This module provides the development entry point for the drowcoder package.
It uses the local project directory (./checkpoints/) for storing checkpoints
during development and testing.
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Type

from .main import Main, MainArgs


def find_project_root() -> Path:
    """Find the project root directory by looking for pyproject.toml"""
    current_dir = Path.cwd()
    project_root = current_dir

    while project_root != project_root.parent:
        if (project_root / 'pyproject.toml').exists():
            return project_root
        project_root = project_root.parent

    # If no pyproject.toml found, use current directory
    return current_dir

@dataclass
class DevArgs(MainArgs):
    config: str = str(find_project_root() / 'configs' / 'config.yaml')
    model: str = None
    workspace: str = None
    checkpoint: str = None
    checkpoint_root: str = str(find_project_root() / 'checkpoints')

class DevMain(Main):
    args: Type[DevArgs] = DevArgs


def main() -> int:
    """CLI entry point function for setuptools console_scripts."""
    return DevMain.run()


if __name__ == "__main__":
    sys.exit(main())
