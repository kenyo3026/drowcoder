import argparse
import litellm
from config_morpher import ConfigMorpher

from drowcoder.agent import DrowAgent
from drowcoder.checkpoint import CHECKPOINT_DEFAULT_NAME
from drowcoder.prompts import *


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default='../configs/config.yaml')
    parser.add_argument("-w", "--workspace", default=None, type=str)
    parser.add_argument("--checkpoint", default=None)
    args = parser.parse_args()

    configs = args.config
    workspace = args.workspace
    checkpoint = args.checkpoint or \
        f'../checkpoints/{CHECKPOINT_DEFAULT_NAME()}'

    config_morpher = ConfigMorpher(configs)

    completion_kwargs = config_morpher.morph(
        litellm.completion,
        start_from='models.[name=claude-4-sonnet]'
    )
    tools = config_morpher.fetch('tools', None)

    agent = DrowAgent(
        workspace=workspace,
        tools=tools,
        checkpoint=checkpoint,
        verbose_style='pretty',
        **completion_kwargs,
    )
    agent.init()
    while True:
        agent.receive()
        agent.complete()