"""
drowcoder Main Module

This module contains the core logic for the drowcoder AI coding assistant.
It provides the main entry point that can be used by different environments
(CLI, development, testing) with different default configurations.
"""

import argparse
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Optional, Type

import litellm
from config_morpher import ConfigMorpher

from .agent import DrowAgent
from .checkpoint import CHECKPOINT_DEFAULT_NAME


def get_version() -> str:
    """Get the package version."""
    try:
        from . import __version__
        return __version__
    except ImportError:
        return "unknown"

@dataclass
class MainArgs:
    config     :str='./config.yaml'
    model      :str=None
    workspace  :str=None
    checkpoint :str=None
    checkpoint_root :str='./checkpoints'

    @classmethod
    def from_args(cls):
        parser = argparse.ArgumentParser()
        parser.add_argument("-c", "--config", default=cls.config)
        parser.add_argument("-m", "--model", default=cls.model)
        parser.add_argument("-w", "--workspace", default=cls.workspace)
        parser.add_argument("--checkpoint", default=cls.checkpoint)
        parser.add_argument("--checkpoint_root", default=cls.checkpoint_root)
        args = parser.parse_args()
        return cls(**args.__dict__)

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
        config = args.config
        model = args.model
        workspace = args.workspace
        checkpoint = args.checkpoint

        # Load configuration
        config_morpher = ConfigMorpher.from_yaml(config)

        completion_kwargs = config_morpher.morph(
            litellm.completion,
            # TODO enable to start_from models[name={model} or model={model}]
            start_from=f'models[model={model}]' if model else f'models[0]',
        )
        tools = config_morpher.fetch('tools', None)

        try:
            # Create and initialize agent
            agent = DrowAgent(
                workspace=workspace,
                tools=tools,
                checkpoint=checkpoint,
                **completion_kwargs,
            )

            agent.init()

            print("DrowCoder AI coding assistant started!")
            print("Type your messages to interact with the agent.")
            print("Press Ctrl+C to exit.\n")

            # Main interaction loop
            while True:
                try:
                    agent.receive()
                    agent.complete()
                except KeyboardInterrupt:
                    print("\n\nExiting DrowCoder. Goodbye!")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    print("Continuing...")

        except Exception as e:
            print(f"Failed to initialize drowcoder: {e}")
            return 1

        return 0


def main() -> int:
    """CLI entry point function for setuptools console_scripts."""
    return Main.run()


if __name__ == "__main__":
    sys.exit(main())
