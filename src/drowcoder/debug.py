"""
Debug Entry Point for drowcoder

This module provides a step-by-step debugging mode for the drowcoder agent.
After each LLM iteration, it pauses and waits for user confirmation ('y')
before continuing to the next step.
"""

import sys
import yaml
import litellm
from dataclasses import dataclass
from typing import Type, Tuple

from config_morpher import ConfigMorpher

from .main import Main
from .develop import DevArgs
from .agent import DrowAgent
from .checkpoint import Checkpoint
from .model import ModelDispatcher
from .utils.logger import enable_rich_logger


@dataclass
class DebugArgs(DevArgs):
    """Debug mode uses same defaults as DevArgs"""
    pass


class DebugMain(Main):
    args: Type[DebugArgs] = DebugArgs

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
        workspace = args.workspace
        checkpoint = args.checkpoint

        checkpoint = Checkpoint(checkpoint)

        logger_path = checkpoint.checkpoint_root / 'logs'
        logger = enable_rich_logger(directory=logger_path)

        # Load configuration
        config_morpher = ConfigMorpher(config)

        models = config_morpher.fetch('models')
        models = ModelDispatcher(models, morph=True)
        completion_kwargs = models.for_chatcompletions.morph(
            litellm.completion,
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

            logger.info("🐛 DrowCoder DEBUG mode started!")
            logger.info("Agent will pause after each iteration and wait for your confirmation.")
            logger.info("Options: (y)continue, (n)stop, (r)show response dict\n")

            if not query:
                query = input("Enter your query: ").strip()
                if not query:
                    logger.error("No query provided. Exiting.")
                    return 1

            # Start debug loop
            agent.receive(query)

            iteration = 0
            while True:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"🔍 DEBUG Iteration {iteration}")
                logger.info(f"{'='*60}\n")

                # Execute one step without recursion
                response_dict, has_tool_calls = cls._step_complete(agent)

                # Wait for user confirmation
                logger.info(f"\n{'='*60}")
                if has_tool_calls:
                    logger.info("⚠️  Tool calls detected. Agent wants to continue.")
                else:
                    logger.info("✅ No tool calls. Agent task may be complete.")

                # Interactive prompt with option to view response
                while True:
                    user_input = input("\n[DEBUG] (y)continue / (n)stop / (r)show response: ").strip().lower()

                    if user_input == 'r':
                        # Display response dict in YAML format
                        logger.info("\n" + "="*60)
                        logger.info("📋 Response Dict:")
                        logger.info("="*60)
                        logger.info(yaml.dump(response_dict, indent=4, allow_unicode=True, sort_keys=False))
                        logger.info("="*60)
                        continue
                    elif user_input == 'y':
                        break
                    elif user_input == 'n':
                        break
                    else:
                        logger.warning("Invalid input. Please enter 'y', 'n', or 'r'.")

                if user_input != 'y':
                    logger.info("🛑 Debug session stopped by user.")
                    break

                if not has_tool_calls:
                    logger.info("✅ No more tool calls. Task completed.")
                    break

            logger.info("\n✨ Debug session ended.")
            return 0

        except KeyboardInterrupt:
            logger.info("\n\n🛑 Debug session interrupted. Goodbye!")
            return 0
        except Exception as e:
            logger.error(f"Failed to run debug mode: {e}")
            import traceback
            traceback.print_exc()
            return 1

    @classmethod
    def _step_complete(cls, agent: DrowAgent) -> Tuple[dict, bool]:
        """
        Execute one completion step without recursion.
        Returns (response_dict, has_tool_calls) tuple.
        """
        completion_kwargs = agent.completion_kwargs

        # Prepare messages (with context pruning if enabled)
        messages = agent._prepare_messages(
            agent.messages,
            last_k_tool_call_group=agent.keep_last_k_tool_call_contexts
        )

        # Call LLM
        response = litellm.completion(messages=messages, **completion_kwargs)
        response_dict = response.to_dict()

        message = response.choices[0].message
        agent.messages.append(message.__dict__)

        # Save to checkpoint
        agent.checkpoint.messages.punch(message.to_dict())
        agent.checkpoint.raw_messages.punch(response_dict)
        agent.verbose_latest_message()

        # Check for tool calls
        has_tool_calls = False
        if message.tool_calls:
            # Execute tool calls
            agent.call_tool(message.tool_calls)
            has_tool_calls = True

        return response_dict, has_tool_calls


def main() -> int:
    """CLI entry point function for debug mode."""
    return DebugMain.run()


if __name__ == "__main__":
    sys.exit(main())

