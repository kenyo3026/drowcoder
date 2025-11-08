import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Union

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.text import Text
from rich.json import JSON
from rich.padding import Padding


@dataclass(frozen=True)
class VerboseStyle:
    SIMPLE: str = 'simple'
    PRETTY: str = 'pretty'
    COMPACT: str = 'compact'
    RICH_PRETTY: str = 'rich_pretty'

    @classmethod
    def get_values(cls) -> List[str]:
        """Get all available verbose style values"""
        instance = cls()
        return [value for value in instance.__dict__.values()]

    @classmethod
    def is_valid(cls, style: str) -> bool:
        """Check if a style string is valid"""
        return style.lower() in cls.get_values()


class BaseMessageVerboser(ABC):
    """Abstract base class for message verbosers"""

    @abstractmethod
    def verbose_message(self, message: Dict[str, Any]) -> None:
        """Display a message in a specific format"""
        pass


class SimpleMessageVerboser(BaseMessageVerboser):
    """Simple message verboser that prints raw message"""

    def verbose_message(self, message: Dict[str, Any]) -> None:
        print(message)


class CompactMessageVerboser(BaseMessageVerboser):
    """Compact message verboser for minimal output"""

    def verbose_message(self, message: Dict[str, Any]) -> None:
        role = message.get('role', 'unknown')
        content = message.get('content', '')

        # Display in compact format
        if role == 'tool':
            func_name = message.get('name', 'unknown')
            print(f"🔧 {func_name}: {content[:50]}{'...' if len(content) > 50 else ''}")
        elif role == 'assistant':
            if message.get('tool_calls'):
                tool_names = [tc.function.name for tc in message.get('tool_calls', [])]
                print(f"🤖 Calling tools: {', '.join(tool_names)}")
            if content:
                print(f"🤖 {content[:80]}{'...' if len(content) > 80 else ''}")
        else:
            print(f"{'👤' if role == 'user' else '🔧'} {content[:80]}{'...' if len(content) > 80 else ''}")


class PrettyMessageVerboser(BaseMessageVerboser):
    """Pretty formatted message verboser with colors and structure"""

    def __init__(self,
                 max_content_length: int = 1000,
                 max_tool_result_length: int = 500,
                 max_arg_length: int = 100,
                 show_colors: bool = True):
        self.max_content_length = max_content_length
        self.max_tool_result_length = max_tool_result_length
        self.max_arg_length = max_arg_length
        self.show_colors = show_colors

        # Set role colors and titles
        self.role_colors = {
            'system': '\033[95m',      # Purple
            'user': '\033[92m',        # Green
            'assistant': '\033[94m',   # Blue
            'tool': '\033[93m'         # Yellow
        } if show_colors else {}

        self.reset_color = '\033[0m' if show_colors else ''

        self.role_titles = {
            'system': '🔧 System',
            'user': '👤 User',
            'assistant': '🤖 Assistant',
            'tool': '⚡ Tool'
        }

    def verbose_message(self, message: Dict[str, Any]) -> None:
        role = message.get('role', 'unknown')

        color = self.role_colors.get(role, '\033[97m' if self.show_colors else '')
        title = self.role_titles.get(role, f'❓ {role.title()}')

        print(f"\n{color}{'='*60}")
        print(f"{title}")
        print(f"{'='*60}{self.reset_color}")

        # Handle different role types
        if role == 'tool':
            self._handle_tool_message(message, color)
        elif role == 'assistant':
            self._handle_assistant_message(message, color)
        else:
            self._handle_general_message(message, color)

        print(f"{color}{'='*60}{self.reset_color}\n")

    def _handle_tool_message(self, message: Dict[str, Any], color: str) -> None:
        """Handle tool response messages"""
        tool_call_id = message.get('tool_call_id', 'N/A')
        func_name = message.get('name', 'N/A')
        arguments = message.get('arguments', {})
        print(f"{color}Tool Call ID :{self.reset_color}{tool_call_id}")

        # print(f"{color}Function:{self.reset_color} {message.get('name', 'N/A')}")
        prefix_pattern = f"Function: "
        prefix_indent = " " * prefix_pattern.__len__()
        prefix_pattern = f"{color}{prefix_pattern}{self.reset_color}"
        self._handle_func_argument_formatting(
            func_name, arguments, prefix_pattern, prefix_indent
        )

        print(f"{color}Result: {self.reset_color}")
        content = message.get('content', '')
        if len(content) > self.max_tool_result_length:
            print(f"{content[:self.max_tool_result_length]}...")
            print(f"[Content truncated - {len(content)} total chars]")
        else:
            print(f"{content}")

    def _handle_assistant_message(self, message: Dict[str, Any], color: str) -> None:
        """Handle assistant messages"""
        content = message.get('content')
        if content:
            print(f"{color}Response:{self.reset_color}")
            print(f"{content}")

        # Handle tool calls
        tool_calls = message.get('tool_calls')
        if tool_calls:
            print(f"\n{color}Tool Calls:{self.reset_color}")
            for i, tool_call in enumerate(tool_calls, 1):
                func_name = tool_call.function.name
                arguments = tool_call.function.arguments

                prefix_pattern = f"  {i}. "
                prefix_indent = " " * prefix_pattern.__len__()
                self._handle_func_argument_formatting(
                    func_name, arguments, prefix_pattern, prefix_indent
                )

    def _handle_general_message(self, message: Dict[str, Any], color: str) -> None:
        """Handle system and user messages"""
        content = message.get('content', '')
        if len(content) > self.max_content_length:
            print(f"{content[:self.max_content_length]}...")
            print(f"[Content truncated - {len(content)} total chars]")
        else:
            print(f"{content}")

    def _handle_func_argument_formatting(
        self,
        func_name: str,
        arguments: Union[str, dict],
        prefix_pattern: str,
        prefix_indent: str,
    ):
        try:
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            if arguments.__len__() == 0:
                print(f"{prefix_pattern}{func_name}()")
            elif arguments.__len__() == 1:
                key, value = next(iter(arguments.items()))
                if isinstance(value, str) and len(value) > self.max_arg_length:
                    value = f"{value[:self.max_arg_length]}..."
                print(f"{prefix_pattern}{func_name}({key}: {value})")
            else:
                print(f"{prefix_pattern}{func_name}(")
                for key, value in arguments.items():
                    if isinstance(value, str) and len(value) > self.max_arg_length:
                        value = f"{value[:self.max_arg_length]}..."
                    print(f"{prefix_indent}\t{key}: {value}")
                print(f"{prefix_indent})")
        except json.JSONDecodeError:
            warning_color = '\033[91m' if self.show_colors else ''
            print(f"{prefix_pattern}{func_name}({warning_color}⚠️  Raw args: {arguments}{self.reset_color})")


class RichPrettyMessageVerboser(BaseMessageVerboser):
    """Rich-based pretty message verboser with enhanced visual appeal"""

    def __init__(self,
                 max_content_length: int = 1000,
                 max_tool_result_length: int = 500,
                 max_arg_length: int = 100,
                 console: Console = None,
                 show_nested: bool = True,
                 debug_mode: bool = False):
        self.max_content_length = max_content_length
        self.max_tool_result_length = max_tool_result_length
        self.max_arg_length = max_arg_length
        self.console = console or Console()
        self.show_nested = show_nested
        self.debug_mode = debug_mode

        # Rich color styles
        self.role_styles = {
            'system': 'bold magenta',
            'user': 'bold green',
            'assistant': 'bold blue',
            'tool': 'bold yellow'
        }

        self.role_titles = {
            'system': '🔧 System',
            'user': '👤 User',
            'assistant': '🤖 Assistant',
            'tool': '⚡ Tool'
        }

        # State tracking for nested display
        # Store tool_call_ids from the most recent assistant message
        self.active_tool_call_ids = set()
        # Track last message role for fallback logic
        self.last_message_role = None
        self.last_message_had_tool_calls = False

    def verbose_message(self, message: Dict[str, Any]) -> None:
        role = message.get('role', 'unknown')
        style = self.role_styles.get(role, 'bold white')
        title = self.role_titles.get(role, f'❓ {role.title()}')

        # Determine indent level with multi-tier fallback strategy
        indent_level = 0
        if self.show_nested and role == 'tool':
            tool_call_id = message.get('tool_call_id')

            # Strategy 1: Precise matching via tool_call_id (most accurate)
            if tool_call_id and tool_call_id in self.active_tool_call_ids:
                indent_level = 1
            # Strategy 2: Fallback - check if previous message was assistant with tool_calls
            elif self.last_message_role == 'assistant' and self.last_message_had_tool_calls:
                indent_level = 1
                # Debug mode: Log warning for ID mismatch
                if self.debug_mode:
                    self.console.print(
                        f"[dim yellow]⚠ Tool call ID '{tool_call_id}' not found in active set "
                        f"{self.active_tool_call_ids}, using fallback strategy[/dim yellow]"
                    )

        # Calculate indent string and tree symbols
        if indent_level > 0:
            # Use tree symbol for nested items
            indent_prefix = "    " * (indent_level)  # Parent indents
            tree_symbol = "└── "
            indent_str = indent_prefix + tree_symbol
        else:
            indent_str = ""

        # Print title bar with simple separator
        self.console.print()  # Empty line before message
        title_text = Text()
        if indent_level > 0:
            # Add indent and tree symbol
            title_text.append(indent_prefix, style="dim")
            title_text.append(tree_symbol, style=style)
        title_text.append("─" * 3 + " ", style=style)
        title_text.append(title, style=style)
        title_text.append(" " + "─" * (70 - len(title) - len(indent_str)), style=style)
        self.console.print(title_text)

        # Handle different role types
        if role == 'tool':
            content = self._render_tool_message(message)
        elif role == 'assistant':
            content = self._render_assistant_message(message)
        else:
            content = self._render_general_message(message)

        # Display content with indentation if needed
        if indent_level > 0:
            # Calculate padding: indent_prefix + space to align with content after tree symbol
            padding_left = len(indent_str)
            padded_content = Padding(content, (0, 0, 0, padding_left))
            self.console.print(padded_content)
        else:
            self.console.print(content)

        # Update state tracking based on message type
        if role == 'assistant':
            # Extract tool_call_ids from this assistant message
            tool_calls = message.get('tool_calls')
            if tool_calls:
                # Store the IDs of tools called by this assistant
                self.active_tool_call_ids = {tc.id for tc in tool_calls}
                self.last_message_had_tool_calls = True
            else:
                # No tool calls, clear the active set
                self.active_tool_call_ids.clear()
                self.last_message_had_tool_calls = False
        elif role == 'user':
            # New user message starts a new conversation turn
            self.active_tool_call_ids.clear()
            self.last_message_had_tool_calls = False

        # Always track the last message role for fallback logic
        self.last_message_role = role

    def _render_tool_message(self, message: Dict[str, Any]) -> Text:
        """Render tool response messages"""
        result = Text()

        tool_call_id = message.get('tool_call_id', 'N/A')
        func_name = message.get('name', 'N/A')
        arguments = message.get('arguments', {})

        # Tool call ID
        result.append("Tool Call ID: ", style="bold")
        result.append(f"{tool_call_id}\n", style="dim")

        # Function signature
        result.append("Function: ", style="bold")
        func_signature = self._format_function_signature(func_name, arguments)
        result.append(func_signature)
        result.append("\n\n")

        # Result
        result.append("Result:\n", style="bold green")
        content = message.get('content', '')
        if len(content) > self.max_tool_result_length:
            result.append(f"{content[:self.max_tool_result_length]}...\n", style="dim")
            result.append(f"[Content truncated - {len(content)} total chars]", style="italic dim")
        else:
            result.append(content, style="")

        return result

    def _render_assistant_message(self, message: Dict[str, Any]) -> Union[Text, Markdown]:
        """Render assistant messages"""
        result = Text()

        # Content (check if it's markdown)
        content = message.get('content')
        if content:
            # Try to render as markdown if it looks like markdown
            if self._looks_like_markdown(content):
                if len(content) > self.max_content_length:
                    content = f"{content[:self.max_content_length]}...\n[Content truncated]"
                return Markdown(content)
            else:
                result.append(content)

        # Tool calls
        tool_calls = message.get('tool_calls')
        if tool_calls:
            if content:
                result.append("\n\n")
            result.append("Tool Calls:\n", style="bold cyan")
            # for i, tool_call in enumerate(tool_calls, 1):
            #     func_name = tool_call.function.name
            #     arguments = tool_call.function.arguments

            #     result.append(f"  {i}. ", style="bold")
            #     func_signature = self._format_function_signature(func_name, arguments)
            #     result.append(func_signature)
            #     if i < len(tool_calls):
            #         result.append("\n")

        return result

    def _render_general_message(self, message: Dict[str, Any]) -> Union[Text, Markdown]:
        """Render system and user messages"""
        content = message.get('content', '')

        # Check if system prompt (usually longer)
        if message.get('role') == 'system' and len(content) > 500:
            if len(content) > self.max_content_length:
                preview = f"{content[:self.max_content_length]}...\n\n"
                preview += f"[System prompt truncated - {len(content)} total chars]"
                return Text(preview, style="dim")
            return Text(content, style="dim")

        # Regular content
        if len(content) > self.max_content_length:
            truncated = f"{content[:self.max_content_length]}...\n"
            truncated += f"[Content truncated - {len(content)} total chars]"
            return Text(truncated)

        return Text(content)

    def _format_function_signature(self, func_name: str, arguments: Union[str, dict]) -> Text:
        """Format function call with arguments"""
        result = Text()
        result.append(func_name, style="bold cyan")

        try:
            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            if not arguments or len(arguments) == 0:
                result.append("()", style="")
            elif len(arguments) == 1:
                key, value = next(iter(arguments.items()))
                if isinstance(value, str) and len(value) > self.max_arg_length:
                    value = f"{value[:self.max_arg_length]}..."
                result.append("(", style="dim")
                result.append(f"{key}", style="yellow")
                result.append("=", style="dim")
                result.append(f"{repr(value)}", style="green")
                result.append(")", style="dim")
            else:
                result.append("(\n", style="dim")
                for i, (key, value) in enumerate(arguments.items()):
                    if isinstance(value, str) and len(value) > self.max_arg_length:
                        value = f"{value[:self.max_arg_length]}..."
                    result.append(f"    {key}", style="yellow")
                    result.append("=", style="dim")
                    result.append(f"{repr(value)}", style="green")
                    if i < len(arguments) - 1:
                        result.append(",\n", style="dim")
                    else:
                        result.append("\n", style="dim")
                result.append("  )", style="dim")

        except json.JSONDecodeError:
            result.append("(", style="dim")
            result.append(f"⚠️ Raw args: {arguments}", style="bold red")
            result.append(")", style="dim")

        return result

    def _looks_like_markdown(self, content: str) -> bool:
        """Simple heuristic to detect markdown content"""
        markdown_indicators = ['#', '```', '**', '*', '- ', '1. ', '[', '](']
        return any(indicator in content for indicator in markdown_indicators)


# Factory function for convenience
class VerboserFactory:
    """Factory class to create message verbosers"""

    @staticmethod
    def get(style: str = 'pretty', **kwargs) -> BaseMessageVerboser:
        """Create verboser instance based on style"""
        if style == 'simple':
            return SimpleMessageVerboser()
        elif style == 'compact':
            return CompactMessageVerboser()
        elif style == 'pretty':
            return PrettyMessageVerboser(**kwargs)
        elif style == 'rich_pretty':
            return RichPrettyMessageVerboser(**kwargs)
        else:
            raise ValueError(f"Unknown verboser style: {style}")

    @staticmethod
    def get_available_styles() -> List[str]:
        """Get all available verboser styles"""
        return VerboseStyle.get_values()


if __name__ == "__main__":

    # Test VerboseStyle
    print(VerboseStyle.get_values())  # ['simple', 'pretty', 'compact']
    print(VerboseStyle.is_valid('pretty'))  # True
    print(VerboseStyle.is_valid('invalid'))  # False
    print(VerboseStyle.PRETTY)  # 'pretty'

    # Test Verboser
    # Initialize test message
    message = {
        'role': 'assistant',
        'content': 'Hello! I can help you with that.',
        'tool_calls': None
    }

    # Test pretty verboser
    pretty = VerboserFactory('pretty')
    pretty.verbose_message(message)

    # Test compact verboser
    compact = VerboserFactory('compact')
    compact.verbose_message(message)