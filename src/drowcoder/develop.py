"""
Development Entry Point for drowcoder

This module provides the development entry point for the drowcoder package.
It uses the local project directory (./checkpoints/) for storing checkpoints
during development and testing.
"""

import sys
from pathlib import Path

from .main import main as main_function


def main() -> int:
    """
    Development entry point.

    Uses ./checkpoints/ as the default checkpoint directory.
    This is intended for use during development and testing.
    """
    # Use local checkpoints directory for development
    current_dir = Path.cwd()

    # Try to find the project root (where pyproject.toml exists)
    project_root = current_dir
    while project_root != project_root.parent:
        if (project_root / 'pyproject.toml').exists():
            break
        project_root = project_root.parent
    else:
        # If no pyproject.toml found, use current directory
        project_root = current_dir

    default_checkpoint_dir = project_root / 'checkpoints'

    return main_function(
        default_checkpoint_dir=default_checkpoint_dir,
        prog_name="drowcoder-dev"
    )


if __name__ == "__main__":
    sys.exit(main())
