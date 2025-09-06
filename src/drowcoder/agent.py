import json
from dataclasses import dataclass
from typing import Union, List, Optional, Dict, Any

import litellm

from .verbose import *
from .tools import tool_manager


@dataclass(frozen=True)
class AgentRole:
    SYSTEM    :str = 'system'
    USER      :str = 'user'
    ASSISTANT :str = 'assistant'
    TOOL      :str = 'tool'


@dataclass
class ToolCallResponse:
    role         :str
    tool_call_id :str
    name         :str
    content      :str

    def form_content(self):
        return '\n'.join([f'**{key}:**\n{value}' for key, value in self.__dict__.items()
                          if not key == 'role'])

    def form_message(self):
        message = self.__dict__
        message['content'] = self.form_content()
        return message


class DrowAgent:

    def __init__(
        self,
        tools: Optional[List[Dict[str, Any]]] = None,
        verbose_style: Union[str, VerboseStyle] = VerboseStyle.PRETTY,
        **completion_kwargs
    ):
        # Apply config tools if provided
        if tools:
            tool_manager.apply_config_tools(tools)

        # Get tools from tool manager
        self.tools = tool_manager.get_tool_descs()
        self.tool_funcs = tool_manager.get_tool_funcs()

        self.messages = []
        self.system_prompt = SystemPromptInstruction.format(tools=self.tools)

        self.completion_kwargs = completion_kwargs
        self.completion_kwargs.update(
            {
                'tools': self.tools,
                'tool_choice': 'auto'
            }
        )

        self.verbose_style = self._resolve_verbose_style(verbose_style)
        self.verboser = VerboserFactory.get(self.verbose_style)

    def _resolve_verbose_style(self, verbose_style):
        """Convert verbose_style to string format"""
        if isinstance(verbose_style, str):
            if VerboseStyle.is_valid(verbose_style):
                return verbose_style.lower()
            else:
                raise ValueError(
                    f"Invalid verbose_style: {verbose_style}. "
                    f"Valid options: {VerboseStyle.get_values()}"
                )
        else:
            return verbose_style

    def init(self):
        if self.system_prompt:
            self.messages.append({"role": AgentRole.SYSTEM, "content": self.system_prompt})

    def call_tool(self, tool_calls:List[litellm.types.utils.ChatCompletionMessageToolCall]):
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            if func_name in self.tool_funcs:
                try:
                    content = self.tool_funcs[func_name](**arguments)
                    content = str(content)
                except Exception as e:
                    content = f"Error executing {func_name}: {str(e)}"
            else:
                content = f"Unknown tool: {func_name}"

            tool_response = ToolCallResponse(
                role = AgentRole.TOOL,
                tool_call_id = tool_call.id,
                name = func_name,
                content = content,
            )

            self.messages.append(tool_response.form_message())
            self.verbose_latest_message()

    def receive(self):
        while True:
            message = input('Input a message: ').strip()
            if message:
                break
        self.messages.append({"role": AgentRole.USER, "content": message})
        self.verbose_latest_message()

    def complete(self):
        message = litellm.completion(messages=self.messages, **self.completion_kwargs)
        message = message.choices[0].message
        self.messages.append(message.__dict__)
        self.verbose_latest_message()

        if message.tool_calls:
            self.call_tool(message.tool_calls)
            self.complete()

    def verbose_latest_message(self):
        if not self.messages:
            return
        message = self.messages[-1]
        self.verboser.verbose_message(message)


if __name__ == "__main__":

    from config_morpher import ConfigMorpher

    from prompts import *

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