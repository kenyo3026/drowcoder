"""
drowcoder Main Module

This module contains the core logic for the drowcoder AI coding assistant.
It provides the main entry point that can be used by different environments
(CLI, development, testing) with different default configurations.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

import litellm

from .agent import DrowAgent
from .checkpoint import CHECKPOINT_DEFAULT_NAME

try:
    from config_morpher import ConfigMorpher
    HAS_CONFIG_MORPHER = True
except ImportError:
    HAS_CONFIG_MORPHER = False
    ConfigMorpher = None


def create_parser(prog_name: str = "drowcoder") -> argparse.ArgumentParser:
    """Create the argument parser for the main function."""
    parser = argparse.ArgumentParser(
        prog=prog_name,
        description="A powerful agentic AI coding assistant framework for Cursor IDE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  drowcoder --workspace /path/to/project
  drowcoder -c config.yaml --checkpoint my_session
  drowcoder --help
        """
    )

    parser.add_argument(
        "-c", "--config",
        type=str,
        default=None,
        help="Path to configuration YAML file"
    )

    parser.add_argument(
        "-w", "--workspace",
        type=str,
        default=None,
        help="Path to workspace directory (default: current directory)"
    )

    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Path to checkpoint directory or name"
    )

    parser.add_argument(
        "--verbose-style",
        type=str,
        choices=["pretty", "plain", "json"],
        default="pretty",
        help="Verbose output style (default: pretty)"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="claude-3-sonnet-20240229",
        help="LLM model to use (default: claude-3-sonnet-20240229)"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"drowcoder {get_version()}"
    )

    return parser


def get_version() -> str:
    """Get the package version."""
    try:
        from . import __version__
        return __version__
    except ImportError:
        return "unknown"


def load_config(config_path: Optional[str]) -> tuple[dict, Optional[list]]:
    """
    Load configuration from YAML file.

    Returns:
        tuple: (completion_kwargs, tools)
    """
    if not config_path or not HAS_CONFIG_MORPHER:
        return {}, None

    try:
        config_morpher = ConfigMorpher.from_yaml(config_path)
        completion_kwargs = config_morpher.morph(
            litellm.completion,
            start_from='models.[name=claude-4-sonnet]'
        )
        tools = config_morpher.fetch('tools', None)
        return completion_kwargs, tools
    except Exception as e:
        print(f"Warning: Failed to load config from {config_path}: {e}")
        return {}, None


def main(
    default_checkpoint_dir: Optional[Path] = None,
    prog_name: str = "drowcoder",
    args: Optional[list] = None
) -> int:
    """
    Main entry point for drowcoder.

    Args:
        default_checkpoint_dir: Default directory for checkpoints
        prog_name: Program name for help messages
        args: Command line arguments (None means use sys.argv)

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    parser = create_parser(prog_name)
    parsed_args = parser.parse_args(args)

    # Load configuration
    completion_kwargs, tools = load_config(parsed_args.config)

    # Set up default model if not in config
    if 'model' not in completion_kwargs:
        completion_kwargs['model'] = parsed_args.model

    # Set up checkpoint path
    checkpoint_path = parsed_args.checkpoint
    if not checkpoint_path:
        if default_checkpoint_dir:
            # Use provided default directory
            checkpoint_dir = Path(default_checkpoint_dir)
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            checkpoint_path = checkpoint_dir / CHECKPOINT_DEFAULT_NAME()
        else:
            # Fallback to current directory
            checkpoint_path = f'checkpoints/{CHECKPOINT_DEFAULT_NAME()}'

    try:
        # Create and initialize agent
        agent = DrowAgent(
            workspace=parsed_args.workspace,
            tools=tools,
            checkpoint=str(checkpoint_path),
            verbose_style=parsed_args.verbose_style,
            **completion_kwargs,
        )

        agent.init()

        print("drowcoder AI coding assistant started!")
        print("Type your messages to interact with the agent.")
        print("Press Ctrl+C to exit.\n")

        # Main interaction loop
        while True:
            try:
                agent.receive()
                agent.complete()
            except KeyboardInterrupt:
                print("\n\nExiting drowcoder. Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                print("Continuing...")

    except Exception as e:
        print(f"Failed to initialize drowcoder: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
