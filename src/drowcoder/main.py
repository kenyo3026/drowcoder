"""
drowcoder Main Module

This module contains the core logic for the drowcoder AI coding assistant.
It provides the main entry point that can be used by different environments
(CLI, development, testing) with different default configurations.
"""

import argparse
import pathlib
import sys
import traceback
from dataclasses import dataclass, field
from typing import List, Type, Union

from config_morpher import ConfigMorpher

from .agent import DrowAgent, litellm
from .checkpoint import Checkpoint, CHECKPOINT_DEFAULT_NAME
from .config import ConfigMain, ConfigCommand
from .model import ModelDispatcher
from .prompts import InstructionType
from .utils.logger import enable_rich_logger


DEFAULT_INSTRUCTION = InstructionType.CODER

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
    config      :Union[str, List[Union[str, pathlib.Path]]] = field(default_factory=lambda: ['./config.yaml'])
    model       :str  = None
    interactive :bool = False
    workspace   :str  = None
    instruction :str  = DEFAULT_INSTRUCTION
    checkpoint  :str  = None
    checkpoint_root :str = './checkpoints'
    disable_rules :bool = False

    # Subcommands
    command    :str=None
    config_action :str=None
    config_file :str=None  # For 'config set' command

    @classmethod
    def from_args(cls):
        parser = argparse.ArgumentParser()

        # Setup primary arguments
        parser.add_argument("-q", "--query", default=cls.query, help="Headless mode: process query directly, otherwise interactive mode")
        parser.add_argument("-c", "--config", default=None, action='append', help="Path list to configuration file")
        parser.add_argument("-m", "--model", default=cls.model, help="Model to use")
        parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
        parser.add_argument("-w", "--workspace", default=cls.workspace, help="Workspace directory")
        parser.add_argument("--instruction", default=cls.instruction, help="System instruction")
        parser.add_argument("--checkpoint", default=cls.checkpoint, help="Checkpoint directory")
        parser.add_argument("--checkpoint_root", default=cls.checkpoint_root, help="Checkpoint root directory")
        parser.add_argument("--disable_rules", action="store_true", dest="disable_rules", help="Disable loading rules from .cursor/rules directory")

        # Setup secondary commands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        # Setup secondary command for config
        parser_for_config = subparsers.add_parser('config', help='Configuration management')
        subparsers_for_config = parser_for_config.add_subparsers(dest='config_action', help='Config actions')
        subparsers_for_config.add_parser('edit', help='Edit configuration file')
        subparsers_for_config.add_parser('validate', help='Validate configuration file')

        parser_show = subparsers_for_config.add_parser('show', help='Show configuration (default: shows default config)')
        parser_show.add_argument('config_file', nargs='?', default=None, help='Path to configuration file (optional)')

        parser_set = subparsers_for_config.add_parser('set', help='Set default configuration file')
        parser_set.add_argument('config_file', help='Path to configuration file')

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
        instruction = args.instruction
        checkpoint = args.checkpoint
        disable_rules = args.disable_rules

        checkpoint = Checkpoint(checkpoint)

        logger_path = checkpoint.checkpoint_root / 'logs'
        logger = enable_rich_logger(directory=logger_path)

        # Load configuration
        config_morpher = ConfigMorpher(config)

        models = config_morpher.fetch('models')
        models = ModelDispatcher(models, morph=True)
        completion_kwargs = models.for_chatcompletions.morph(
            litellm.completion,
            # TODO enable to start_from models[name={model} or model={model}]
            start_from=f'models[model={model}]' if model else f'models[0]',
        )

        postcompletion_kwargs, postcompletion_task = {}, None
        if models.for_postcompletions and models.for_postcompletions.fetch('models'):
            postcompletion_kwargs = models.for_postcompletions.morph(
                litellm.completion,
                # TODO enable to start_from models[name={model} or model={model}]
                start_from=f'models[model={model}]' if model else f'models[0]',
            )
            postcompletion_task = models.for_postcompletions.fetch(
                (f'models[model={model}]' if model else f'models[0]') + '.roles.postcompletions'
            )

        instruction = config_morpher.fetch('instruction', instruction)
        tools = config_morpher.fetch('tools', None)
        mcps = config_morpher.fetch('mcps', None)
        rules = config_morpher.fetch('rules', None)

        try:
            # Create and initialize agent
            agent = DrowAgent(
                workspace=workspace,
                instruction=instruction,
                tools=tools,
                mcps=mcps,
                rules=rules,
                disable_rules=disable_rules,
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
                        logger.exception(f"Post-completion failed: {e}")
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
                                logger.exception(f"Post-completion failed: {e}")

                    except KeyboardInterrupt:
                        logger.info("\n\nExiting DrowCoder. Goodbye!")
                        break
                    except Exception as e:
                        logger.exception(f"Error: {e}")
                        logger.info("Continuing...")

        except Exception as e:
            logger.exception(f"Failed to initialize drowcoder: {e}")
            logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            return 1

        return 0

    @classmethod
    def run_config(cls, args):
        """Handle config subcommands"""
        config_action = args.config_action

        if config_action == ConfigCommand.SET:
            # For 'set', use the config_file argument
            return ConfigMain.set(args.config_file)
        elif config_action == ConfigCommand.SHOW:
            # For 'show', use config_file if provided, otherwise None (shows default)
            return ConfigMain.show(getattr(args, 'config_file', None))

        # For other commands, use the config path
        config_path = args.config

        if config_action == ConfigCommand.EDIT:
            return ConfigMain.edit(config_path)
        elif config_action == ConfigCommand.VALIDATE:
            return ConfigMain.validate(config_path)
        else:
            # Note: No logger available in config subcommands, fallback to print
            print("Usage: drowcoder config {edit|show|validate|set}")
            return 1


def main() -> int:
    """CLI entry point function for setuptools console_scripts."""
    return Main.run()


if __name__ == "__main__":
    sys.exit(main())
