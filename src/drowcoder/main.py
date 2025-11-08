"""
drowcoder Main Module

This module contains the core logic for the drowcoder AI coding assistant.
It provides the main entry point that can be used by different environments
(CLI, development, testing) with different default configurations.
"""

import argparse
import pathlib
import sys
from dataclasses import dataclass
from typing import Type

import litellm
from config_morpher import ConfigMorpher

from .agent import DrowAgent
from .checkpoint import Checkpoint, CHECKPOINT_DEFAULT_NAME
from .config import ConfigMain, ConfigCommand
from .model import ModelDispatcher
from .utils.logger import enable_rich_logger


def get_version() -> str:
    """Get the package version."""
    try:
        from . import __version__
        return __version__
    except ImportError:
        return "unknown"

@dataclass
class MainArgs:
    # Primary arguments
    query       :str  = None
    config      :str  = './config.yaml'
    model       :str  = None
    interactive :bool = False
    workspace   :str  = None
    checkpoint  :str  = None
    checkpoint_root :str = './checkpoints'

    # Subcommands
    command    :str=None
    config_action :str=None

    @classmethod
    def from_args(cls):
        parser = argparse.ArgumentParser()

        # Setup primary arguments
        parser.add_argument("-q", "--query", default=cls.query, help="Headless mode: process query directly, otherwise interactive mode")
        parser.add_argument("-c", "--config", default=cls.config, help="Path to configuration file")
        parser.add_argument("-m", "--model", default=cls.model, help="Model to use")
        parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
        parser.add_argument("-w", "--workspace", default=cls.workspace, help="Workspace directory")
        parser.add_argument("--checkpoint", default=cls.checkpoint, help="Checkpoint directory")
        parser.add_argument("--checkpoint_root", default=cls.checkpoint_root, help="Checkpoint root directory")

        # Setup secondary commands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        # Setup secondary command for config
        parser_for_config = subparsers.add_parser('config', help='Configuration management')
        subparsers_for_config = parser_for_config.add_subparsers(dest='config_action', help='Config actions')
        subparsers_for_config.add_parser('edit', help='Edit configuration file')
        subparsers_for_config.add_parser('show', help='Show current configuration')
        subparsers_for_config.add_parser('validate', help='Validate configuration file')

        args = parser.parse_args()
        return cls(**{k: v for k, v in args.__dict__.items() if hasattr(cls, k)})

    def __post_init__(self):
        if not self.checkpoint:
            self.checkpoint = CHECKPOINT_DEFAULT_NAME()
        self.checkpoint = pathlib.Path(self.checkpoint)

        if not self.checkpoint.is_absolute():
            self.checkpoint_root = pathlib.Path(self.checkpoint_root)
            self.checkpoint = self.checkpoint_root / self.checkpoint

        pathlib.Path(self.checkpoint).mkdir(parents=True, exist_ok=True)

class Main:
    args:Type[MainArgs] = MainArgs

    @classmethod
    def run(cls):
        args = cls.args.from_args()

        # Handle config subcommands
        if args.command == 'config':
            return cls.run_config(args)

        # Regular execution
        query = args.query
        config = args.config
        model = args.model
        interactive = args.interactive if query else True
        workspace = args.workspace
        checkpoint = args.checkpoint

        checkpoint = Checkpoint(checkpoint)

        logger_path = checkpoint.checkpoint_root / 'logs'
        logger = enable_rich_logger(directory=logger_path)

        # Load configuration
        config_morpher = ConfigMorpher.from_yaml(config)

        models = config_morpher.fetch('models')
        models = ModelDispatcher(models, morph=True)
        completion_kwargs = models.for_chatcompletions.morph(
            litellm.completion,
            # TODO enable to start_from models[name={model} or model={model}]
            start_from=f'models[model={model}]' if model else f'models[0]',
        )

        postcompletion_kwargs, postcompletion_task = {}, None
        if models.for_postcompletions:
            postcompletion_kwargs = models.for_postcompletions.morph(
                litellm.completion,
                # TODO enable to start_from models[name={model} or model={model}]
                start_from=f'models[model={model}]' if model else f'models[0]',
            )
            postcompletion_task = models.for_postcompletions.fetch(
                (f'models[model={model}]' if model else f'models[0]') + '.roles.postcompletions'
            )

        tools = config_morpher.fetch('tools', None)

        try:
            # Create and initialize agent
            agent = DrowAgent(
                workspace=workspace,
                tools=tools,
                checkpoint=checkpoint,
                logger=logger,
                **completion_kwargs,
            )

            agent.init()

            logger.info("DrowCoder AI coding assistant started!")
            logger.info("Type your messages to interact with the agent.")
            logger.info("Press Ctrl+C to exit.\n")

            if query and not interactive:
                # Headless mode: process query once and exit
                agent.receive(query)
                agent.complete()

                # TODO: Support independent agent instances for post-completion tasks in the future works
                #       - isolated context (no message inheritance from completion)
                if postcompletion_task:
                    logger.info(f"🔄 Post-completion: {postcompletion_task[:50]}{'...' if len(postcompletion_task) > 50 else ''}")
                    try:
                        agent.receive(postcompletion_task)
                        agent.complete(**postcompletion_kwargs)
                    except Exception as e:
                        logger.error(f"Post-completion failed: {e}")
            else:
                # Interactive/Hybrid mode: continuous loop with optional initial query
                while True:
                    try:
                        agent.receive(query)
                        agent.complete()
                        query = None  # Clear query to switch to interactive mode

                        # TODO: Support independent agent instances for post-completion tasks in the future works
                        #       - isolated context (no message inheritance from completion)
                        if postcompletion_task:
                            logger.info(f"🔄 Post-completion: {postcompletion_task[:50]}{'...' if len(postcompletion_task) > 50 else ''}")
                            try:
                                agent.receive(postcompletion_task)
                                agent.complete(**postcompletion_kwargs)
                            except Exception as e:
                                logger.error(f"Post-completion failed: {e}")

                    except KeyboardInterrupt:
                        logger.info("\n\nExiting DrowCoder. Goodbye!")
                        break
                    except Exception as e:
                        logger.error(f"Error: {e}")
                        logger.info("Continuing...")

        except Exception as e:
            logger.error(f"Failed to initialize drowcoder: {e}")
            return 1

        return 0

    @classmethod
    def run_config(cls, args):
        """Handle config subcommands"""
        config_path = args.config
        config_action = args.config_action

        if config_action == ConfigCommand.EDIT:
            return ConfigMain.edit(config_path)
        elif config_action == ConfigCommand.SHOW:
            return ConfigMain.show(config_path)
        elif config_action == ConfigCommand.VALIDATE:
            return ConfigMain.validate(config_path)
        else:
            # Note: No logger available in config subcommands, fallback to print
            print("Usage: drowcoder config {edit|show|validate}")
            return 1


def main() -> int:
    """CLI entry point function for setuptools console_scripts."""
    return Main.run()


if __name__ == "__main__":
    sys.exit(main())
