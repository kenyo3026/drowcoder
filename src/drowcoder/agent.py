import os
import json
import logging
import pathlib
from dataclasses import dataclass
from typing import Union, List, Optional, Dict, Any

import litellm

from .checkpoint import Checkpoint
from .prompts import *
from .tools.dispatcher import Dispatcher
from .verbose import *
from .utils.logger import OutputCapture
from .utils.unique_id import generate_unique_id
from .utils.error_handler import suppress_errors


DROWAGENT_DIR = pathlib.Path('.drowcoder')
DROWAGENT_RULES_DIR = DROWAGENT_DIR / 'rules'

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
    captured_logs      :str = ""

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
        mcps: Optional[Dict[str, Any]] = None,
        rules: Optional[Union[str, pathlib.Path, List[Union[str, pathlib.Path]]]] = None,
        disable_rules: bool = False,
        keep_last_k_tool_call_contexts:int = 5,
        logger: Optional[logging.Logger] = None,
        checkpoint: Union[str, Checkpoint] = None,
        verbose_style: Union[str, VerboseStyle] = VerboseStyle.RICH_PRETTY,
        max_iterations: int = 50,
        max_iterations_without_call_tools: int = 3,
        **completion_kwargs
    ):
        """
        Initialize DrowAgent with workspace, tools, and configuration.

        Args:
            workspace: Workspace directory path
            tools: Optional list of tool configurations in OpenAI format.
                If provided, these tools will override/extend default builtin tools.
                Format: [{"type": "function", "function": {...}}, ...]
            mcps: Optional dict of MCP (Model Context Protocol) servers configuration.
                If provided, these MCP servers will be loaded and their tools made available.
                Supports two formats:
                1. Normal format:
                   {"server_name": {"url": "...", "headers": {...}}, ...}
                2. Nested format:
                   {"mcps": {"server_name": {"url": "...", "headers": {...}}, ...}}
            rules: Optional path(s) to rule file(s) or directory(ies) containing .mdc files.
                Can be a single path (str or pathlib.Path) or a list of paths.
                Default: workspace/.drowcoder/rules directory is always included unless disabled.
            disable_rules: If True, disable all rule loading (including default workspace rules).
                Default: False
            keep_last_k_tool_call_contexts: Number of tool call contexts to keep
            logger: Optional logger instance
            checkpoint: Checkpoint directory or Checkpoint instance
            verbose_style: Verbose output style
            max_iterations: Maximum number of iterations
            max_iterations_without_call_tools: Max iterations without tool calls
            **completion_kwargs: Additional arguments for completion API
        """
        self.logger = logger or logging.getLogger(__name__)

        self.setup_workspace(workspace)
        self.setup_rules(rules, disable_rules)

        self.checkpoint = checkpoint
        if isinstance(self.checkpoint, str) or self.checkpoint is None:
            self.checkpoint = Checkpoint(self.checkpoint)

        # Initialize tool dispatcher with default builtin tools
        # When configs=None, ToolDispatcher automatically loads DEFAULT_TOOL_CONFIGS
        # This ensures default tools are always available
        dispatcher = Dispatcher(
            logger=self.logger,
            checkpoint=self.checkpoint.checkpoint_root,
        )

        # Apply user-provided tools to override/extend default tools
        # If tools is provided, it will update existing tools with same name
        # or add new tools to the dispatcher
        if tools:
            dispatcher.apply_tools(
                configs=tools,
            )
        if mcps:
            dispatcher.apply_mcps(
                configs=mcps,
            )

        # Extract tool descriptions and functions for agent use
        self.tools = dispatcher.expose_descs()
        self.tool_funcs = dispatcher.expose_funcs()
        self.tool_call_group_ids = []
        self.keep_last_k_tool_call_contexts = keep_last_k_tool_call_contexts

        # Iteration control - agent will keep iterating until one of:
        # 1. max_iterations is reached (total iteration limit), OR
        # 2. attempt_completion is called (explicit completion signal), OR
        # 3. max_iterations_without_call_tools is reached (continuous thinking without tools)
        #    - Set to 0 for Cursor-like behavior (stop immediately without tools)
        #    - Set to 3+ for allowing extended thinking chains
        self.max_iterations = max_iterations
        self.max_iterations_without_call_tools = max_iterations_without_call_tools
        self.iteration_so_far = 0
        self.iteration_so_far_without_call_tools = 0

        self.messages = []
        self.system_prompt = ''
        with suppress_errors(self.logger):
            self.system_prompt = SystemPromptInstruction.format(
                tools=self.tools,
                rules=self.rules,
            )

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

    def setup_rules(
        self,
        rules: Optional[Union[str, pathlib.Path, List[Union[str, pathlib.Path]]]] = None,
        disable_rules: bool = False
    ):
        if disable_rules:
            # When rules are disabled, use empty list
            self.rules = []
        else:
            # Start with default workspace rules directory
            self.rules = [pathlib.Path(self.workspace) / DROWAGENT_RULES_DIR]

            # Add user-provided rules if any
            if rules:
                if isinstance(rules, list):
                    self.rules.extend(pathlib.Path(rule) for rule in rules)
                elif isinstance(rules, (str, pathlib.Path)):
                    self.rules.append(pathlib.Path(rules))
                else:
                    raise TypeError(
                        f"rules must be str, pathlib.Path, or List[str, pathlib.Path], "
                        f"got {type(rules).__name__}"
                    )

    def call_tool(self, tool_calls:List[litellm.types.utils.ChatCompletionMessageToolCall]):
        tool_call_group_id = generate_unique_id(length=8)
        self.tool_call_group_ids.append(tool_call_group_id)

        for tool_call in tool_calls:
            func_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            if func_name in self.tool_funcs:
                # Use OutputCapture to capture logger output during tool execution
                try:
                    with OutputCapture(logger=self.logger) as capture:
                        content = self.tool_funcs[func_name](**arguments)
                    content = str(content)

                    # Get captured logs
                    captured_output = capture.get_output()
                    captured_logs = captured_output['logs']

                except Exception as e:
                    content = f"Error executing {func_name}: {str(e)}"
                    # Try to get partial logs if capture was initiated
                    try:
                        captured_output = capture.get_output()
                        captured_logs = captured_output['logs']
                    except:
                        captured_logs = ""
            else:
                content = f"Unknown tool: {func_name}"
                captured_logs = ""

            tool_response = ToolCallResponse(
                role = AgentRole.TOOL,
                tool_call_id = tool_call.id,
                tool_call_group_id = tool_call_group_id,
                name = func_name,
                arguments = arguments,
                content = content,
                captured_logs = captured_logs,
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
        self.iteration_so_far = 0
        self.iteration_so_far_without_call_tools = 0

        message = {"role": AgentRole.USER, "content": content}
        self.messages.append(message)

        self.checkpoint.messages.punch(message)
        self.checkpoint.raw_messages.punch(message)
        self.verbose_latest_message()

    def complete(self, **completion_kwargs):
        # Increment iteration counter
        self.iteration_so_far += 1

        # Stop condition 1: Check max iterations
        if self.iteration_so_far > self.max_iterations:
            warning_msg = (
                f"⚠️  Reached maximum iterations ({self.max_iterations}). "
                f"Agent did not call attempt_completion."
            )
            self.logger.warning(warning_msg)
            return

        completion_kwargs = {**self.completion_kwargs, **completion_kwargs}

        messages = self._prepare_messages(self.messages, last_k_tool_call_group=self.keep_last_k_tool_call_contexts)

        response = litellm.completion(messages=messages, **completion_kwargs)
        message = response.choices[0].message

        if all(getattr(message, attr, None) is None for attr in ['content', 'tool_calls', 'thinking_blocks']):
            finish_reason = response.choices[0].finish_reason or 'unknown'
            message.content = f"Empty response. Finish reason: {finish_reason}"

        self.messages.append(message.__dict__)

        # look out -> message.__dict__ != message.to_dict()
        self.checkpoint.messages.punch(message.to_dict())
        self.checkpoint.raw_messages.punch(response.to_dict())
        self.verbose_latest_message()

        # Stop condition 2: Check if task is explicitly marked as completed
        if self._is_task_completed(message):
            completion_msg = "✓ Task completed - agent called attempt_completion"
            self.logger.info(completion_msg)
            return

        # Execute tools if any
        if message.tool_calls:
            self.call_tool(message.tool_calls)
            self.iteration_so_far_without_call_tools = 0
        else:
            self.iteration_so_far_without_call_tools += 1

            # Stop if exceeded max continuous iterations without tools
            # max=0: stop immediately (Cursor mode)
            # max=3: allow 3 iterations, stop on 4th
            if self.iteration_so_far_without_call_tools > self.max_iterations_without_call_tools:
                warning_msg = (
                    f"⚠️  Reached maximum iterations ({self.max_iterations_without_call_tools}) without calling tools. "
                    f"Agent stopped to prevent excessive thinking loops. Task may not be completed - consider calling attempt_completion if finished, or use tools to make progress."
                )
                self.logger.warning(warning_msg)
                return

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
