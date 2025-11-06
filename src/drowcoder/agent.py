import os
import json
import pathlib
from dataclasses import dataclass
from functools import partial
from typing import Union, List, Optional, Dict, Any

import litellm

from .checkpoint import Checkpoint
from .prompts import *
from .tools import ToolManager
from .verbose import *
from .utils.unique_id import generate_unique_id


@dataclass(frozen=True)
class AgentRole:
    SYSTEM    :str = 'system'
    USER      :str = 'user'
    ASSISTANT :str = 'assistant'
    TOOL      :str = 'tool'


@dataclass
class ToolCallResponse:
    role               :str
    tool_call_id       :str
    tool_call_group_id :str
    name               :str
    arguments          :dict
    content            :str

    def form_content(self):
        return '\n'.join([f'**{key}:**\n{value}' for key, value in self.__dict__.items()
                          if not key == 'role'])

    def form_message(self):
        message = self.__dict__
        # message['content'] = self.form_content()
        return message


class DrowAgent:

    def __init__(
        self,
        workspace: str = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        keep_last_k_tool_call_contexts:int = 5,
        checkpoint: Union[str, Checkpoint] = None,
        verbose_style: Union[str, VerboseStyle] = VerboseStyle.PRETTY,
        max_iterations: int = 50,
        **completion_kwargs
    ):
        self.setup_workspace(workspace)

        self.checkpoint = checkpoint
        if isinstance(self.checkpoint, str) or self.checkpoint is None:
            self.checkpoint = Checkpoint(self.checkpoint)

        # Apply config tools if provided
        tool_manager = ToolManager(
            checkpoint=self.checkpoint.checkpoint_root,
        )
        if tools:
            tool_manager.apply_config_tools(tools)

        # Get tools from tool manager
        self.tools = tool_manager.get_tool_descs()
        self.tool_funcs = tool_manager.get_tool_funcs()
        self.tool_call_group_ids = []
        self.keep_last_k_tool_call_contexts = keep_last_k_tool_call_contexts

        # Iteration control - agent will keep iterating until:
        # 1. max_iterations is reached, OR
        # 2. attempt_completion is called
        self.max_iterations = max_iterations
        self.current_iteration = 0

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
            message = {"role": AgentRole.SYSTEM, "content": self.system_prompt}
            self.messages.append(message)

            self.checkpoint.messages.punch(message)
            self.checkpoint.raw_messages.punch(message)

    def setup_workspace(self, workspace: str):
        workspace = pathlib.Path(workspace or os.getcwd()).resolve()

        if not workspace.exists():
            raise ValueError(f"Workspace does not exist: {workspace}")

        if not workspace.is_dir():
            raise ValueError(f"Workspace is not a directory: {workspace}")

        # Check I/O permission
        if not os.access(workspace, os.R_OK | os.W_OK):
            raise PermissionError(f"No read/write access to workspace: {workspace}")

        self.workspace = workspace

    def call_tool(self, tool_calls:List[litellm.types.utils.ChatCompletionMessageToolCall]):
        tool_call_group_id = generate_unique_id(length=8)
        self.tool_call_group_ids.append(tool_call_group_id)

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
                tool_call_group_id = tool_call_group_id,
                name = func_name,
                arguments = arguments,
                content = content,
            )
            message = tool_response.form_message()

            self.messages.append(message)
            self.checkpoint.messages.punch(message)
            self.checkpoint.raw_messages.punch(message)
            self.verbose_latest_message()

    def receive(self, content:str=None):
        if not content:
            while True:
                content = input('Input a message: ').strip()
                if content: break

        if not isinstance(content, str):
            raise TypeError(f"Expected string for content, got {type(content).__name__} instead")

        # Reset iteration counter for new user message
        self.current_iteration = 0

        message = {"role": AgentRole.USER, "content": content}
        self.messages.append(message)

        self.checkpoint.messages.punch(message)
        self.checkpoint.raw_messages.punch(message)
        self.verbose_latest_message()

    def complete(self, **completion_kwargs):
        # Increment iteration counter
        self.current_iteration += 1

        # Stop condition 1: Check max iterations
        if self.current_iteration > self.max_iterations:
            warning_msg = (
                f"⚠️  Reached maximum iterations ({self.max_iterations}). "
                f"Agent did not call attempt_completion."
            )
            print(f"\n{warning_msg}")
            return

        completion_kwargs = {**self.completion_kwargs, **completion_kwargs}

        messages = self._prepare_messages(self.messages, last_k_tool_call_group=self.keep_last_k_tool_call_contexts)

        response = litellm.completion(messages=messages, **completion_kwargs)
        message = response.choices[0].message
        self.messages.append(message.__dict__)

        # look out -> message.__dict__ != message.to_dict()
        self.checkpoint.messages.punch(message.to_dict())
        self.checkpoint.raw_messages.punch(response.to_dict())
        self.verbose_latest_message()

        # Stop condition 2: Check if task is explicitly marked as completed
        if self._is_task_completed(message):
            completion_msg = "✓ Task completed - agent called attempt_completion"
            print(f"\n{completion_msg}")
            return

        # Execute tools if any
        if message.tool_calls:
            self.call_tool(message.tool_calls)

        # KEY CHANGE: Always continue iterating (no longer depend on tool_calls)
        # Agent will keep thinking until it calls attempt_completion or hits max_iterations
        self.complete()

    def verbose_latest_message(self):
        if not self.messages:
            return
        message = self.messages[-1]
        self.verboser.verbose_message(message)

    def _is_task_completed(self, message) -> bool:
        """
        Check if the agent has marked the task as completed.

        This is the explicit stopping signal - when the agent calls
        attempt_completion, it means it considers the task done.

        Args:
            message: The assistant message to check

        Returns:
            bool: True if attempt_completion was called, False otherwise
        """
        if not hasattr(message, 'tool_calls') or not message.tool_calls:
            return False

        return any(
            tool_call.function.name == 'attempt_completion'
            for tool_call in message.tool_calls
        )

    def _prepare_messages(self, messages, **kwargs):
        if self.tool_call_group_ids:
            messages = self._prepare_tool_messages(messages, **kwargs)
        return messages

    def _prepare_tool_messages(self, messages, last_k_tool_call_group:int=1, **kwargs):
        if last_k_tool_call_group > 0:
            last_k_tool_call_group = min(last_k_tool_call_group, len(self.tool_call_group_ids))

            _group_id_for_break = self.tool_call_group_ids[-last_k_tool_call_group]
            _messages_for_llm, _flag_for_pop = [], True
            for message in messages:
                if message.get('role') == AgentRole.TOOL and message.get('tool_call_group_id') == _group_id_for_break:
                    _flag_for_pop = False
                if message.get('role') == AgentRole.TOOL and _flag_for_pop:
                    continue
                _messages_for_llm.append(message)
            return _messages_for_llm

        elif last_k_tool_call_group == 0:  # ignore all tool messages for llm
            return [message for message in messages if message.get('role') != AgentRole.TOOL]

        elif last_k_tool_call_group == -1: # keep all tool messages for llm
            return messages

        else:
            raise ValueError(f"Invalid last_k_tool_call_group: {last_k_tool_call_group}. Must be > 0 or -1.")
