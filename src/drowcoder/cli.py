"""
CLI Entry Point for drowcoder (Production Environment)

This module provides the CLI entry point for the installed drowcoder package.
It uses the standard user directory (~/.drowcoder/checkpoints/) for storing checkpoints.
"""

import sys
from pathlib import Path

from .main import main as main_function


def main() -> int:
    """
    Production CLI entry point.

    Uses ~/.drowcoder/checkpoints/ as the default checkpoint directory.
    This is the entry point called when users run 'drowcoder' command.
    """
    # Use user home directory for production checkpoints
    default_checkpoint_dir = Path.home() / '.drowcoder' / 'checkpoints'

    return main_function(
        default_checkpoint_dir=default_checkpoint_dir,
        prog_name="drowcoder"
    )


if __name__ == "__main__":
    sys.exit(main())
