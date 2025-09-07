import litellm
from config_morpher import ConfigMorpher

from drowcoder.prompts import *
from drowcoder.agent import DrowAgent


if __name__ == '__main__':

    DEMO_CONFIG_PATH = '../configs/config.yaml'
    configs = DEMO_CONFIG_PATH
    config_morpher = ConfigMorpher.from_yaml(configs)

    completion_kwargs = config_morpher.morph(
        litellm.completion,
        start_from='models.[name=claude-4-sonnet]'
    )
    tools = config_morpher.fetch('tools', None)

    agent = DrowAgent(
        tools=tools,
        verbose_style='pretty',
        **completion_kwargs,
    )
    agent.init()
    while True:
        agent.receive()
        agent.complete()