import litellm
from config_morpher import ConfigMorpher

from drowcoder.agent import DrowAgent
from drowcoder.checkpoint import CHECKPOINT_DEFAULT_NAME
from drowcoder.prompts import *


if __name__ == '__main__':

    checkpoint = f'../checkpoints/{CHECKPOINT_DEFAULT_NAME()}'

    configs = '../configs/config.yaml'
    config_morpher = ConfigMorpher.from_yaml(configs)

    completion_kwargs = config_morpher.morph(
        litellm.completion,
        start_from='models.[name=claude-4-sonnet]'
    )
    tools = config_morpher.fetch('tools', None)

    agent = DrowAgent(
        tools=tools,
        checkpoint=checkpoint,
        verbose_style='pretty',
        **completion_kwargs,
    )
    agent.init()
    while True:
        agent.receive()
        agent.complete()