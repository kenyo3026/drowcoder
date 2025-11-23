# Verbose System

## Overview

The `verbose` module provides a flexible message output system for drowcoder agents. It offers multiple output styles ranging from simple text to rich formatted displays, allowing users to customize how agent messages, tool calls, and responses are displayed.

## Features

- **Multiple Output Styles**: Four distinct styles (simple, compact, pretty, rich_pretty)
- **Rich Formatting**: Enhanced visual appeal with colors, panels, and structured layouts
- **Tool Call Visualization**: Special handling for tool calls with nested display
- **Content Truncation**: Automatic truncation for long content with configurable limits
- **Markdown Support**: Automatic markdown detection and rendering
- **Extensible Architecture**: Easy to add custom verboser implementations

## Verbose Styles

### Simple Style

Minimal output that prints raw message dictionaries.

```python
from drowcoder import VerboserFactory

verboser = VerboserFactory.get('simple')
verboser.verbose_message({'role': 'user', 'content': 'Hello'})
```

**Use Case**: Debugging or when you need raw message data.

### Compact Style

Minimal output with emoji indicators and truncated content.

```python
verboser = VerboserFactory.get('compact')
verboser.verbose_message({'role': 'assistant', 'content': 'Response...'})
```

**Output Example**:
```
🤖 Response content here...
🔧 execute_cmd: Command output...
```

**Use Case**: Quick overview without detailed formatting.

### Pretty Style

Formatted output with colors and structured layout using ANSI color codes.

```python
verboser = VerboserFactory.get('pretty')
verboser.verbose_message({
    'role': 'assistant',
    'content': 'Hello!',
    'tool_calls': [...]
})
```

**Features**:
- Color-coded roles (system, user, assistant, tool)
- Structured function call formatting
- Content truncation with length indicators
- Configurable length limits

**Configuration Options**:
- `max_content_length`: Maximum content length (default: 1000)
- `max_tool_result_length`: Maximum tool result length (default: 500)
- `max_arg_length`: Maximum argument length (default: 100)
- `show_colors`: Enable/disable colors (default: True)

### Rich Pretty Style (Default)

Enhanced formatting using the Rich library with advanced visual features.

```python
verboser = VerboserFactory.get('rich_pretty')
verboser.verbose_message({
    'role': 'tool',
    'name': 'execute',
    'content': 'Command output...'
})
```

**Features**:
- Rich library integration for advanced formatting
- Nested tool call display with tree structure
- Automatic markdown rendering
- Syntax highlighting for code
- Panel-based layouts
- State tracking for tool call relationships

**Configuration Options**:
- `max_content_length`: Maximum content length (default: 1000)
- `max_tool_result_length`: Maximum tool result length (default: 500)
- `max_arg_length`: Maximum argument length (default: 100)
- `console`: Custom Rich Console instance (optional)
- `show_nested`: Enable nested tool call display (default: True)
- `debug_mode`: Enable debug logging (default: False)

## Usage

### Basic Usage

```python
from drowcoder import VerboserFactory, VerboseStyle

# Create verboser with default style
verboser = VerboserFactory.get()

# Create verboser with specific style
verboser = VerboserFactory.get('rich_pretty')

# Create verboser with custom configuration
verboser = VerboserFactory.get(
    'pretty',
    max_content_length=2000,
    show_colors=False
)
```

### Using with Agent

The verbose system is automatically integrated with `DrowAgent`:

```python
from drowcoder import DrowAgent, VerboseStyle

# Use default style (rich_pretty)
agent = DrowAgent(
    workspace='./project',
    verbose_style=VerboseStyle.RICH_PRETTY
)

# Use compact style
agent = DrowAgent(
    workspace='./project',
    verbose_style='compact'
)

# Use string directly
agent = DrowAgent(
    workspace='./project',
    verbose_style='pretty'
)
```

### Custom Verboser Configuration

```python
from drowcoder import VerboserFactory
from rich.console import Console

# Create custom Rich console
custom_console = Console(force_terminal=True, width=120)

# Create verboser with custom console
verboser = VerboserFactory.get(
    'rich_pretty',
    console=custom_console,
    max_content_length=5000,
    show_nested=True,
    debug_mode=True
)
```

## API Reference

### VerboseStyle

Constants for verbose style values.

```python
@dataclass(frozen=True)
class VerboseStyle:
    SIMPLE: str = 'simple'
    PRETTY: str = 'pretty'
    COMPACT: str = 'compact'
    RICH_PRETTY: str = 'rich_pretty'
```

**Class Methods**:
- `get_values() -> List[str]`: Get all available style values
- `is_valid(style: str) -> bool`: Check if a style string is valid

### VerboserFactory

Factory class for creating verboser instances.

#### `get(style: str = 'pretty', **kwargs) -> BaseMessageVerboser`

Create a verboser instance based on style.

**Parameters**:
- **`style`** (str): Style name - `'simple'`, `'compact'`, `'pretty'`, or `'rich_pretty'` (default: `'pretty'`)
- **`**kwargs`**: Style-specific configuration options

**Returns**: `BaseMessageVerboser` instance

**Raises**: `ValueError` if style is unknown

#### `get_available_styles() -> List[str]`

Get all available verboser style names.

**Returns**: List of available style strings

### BaseMessageVerboser

Abstract base class for all verbosers.

#### `verbose_message(message: Dict[str, Any]) -> None`

Display a message in the verboser's format.

**Parameters**:
- **`message`** (Dict[str, Any]): Message dictionary with keys:
  - `role`: Message role (`'system'`, `'user'`, `'assistant'`, `'tool'`)
  - `content`: Message content (string)
  - `tool_calls`: List of tool calls (for assistant messages)
  - `name`: Tool name (for tool messages)
  - `tool_call_id`: Tool call ID (for tool messages)
  - `arguments`: Tool arguments (for tool messages)

## Message Format Examples

### User Message

```python
message = {
    'role': 'user',
    'content': 'What is Python?'
}
verboser.verbose_message(message)
```

### Assistant Message with Tool Calls

```python
message = {
    'role': 'assistant',
    'content': 'I will search for information about Python.',
    'tool_calls': [
        {
            'id': 'call_123',
            'function': {
                'name': 'search',
                'arguments': '{"query": "Python programming"}'
            }
        }
    ]
}
verboser.verbose_message(message)
```

### Tool Response Message

```python
message = {
    'role': 'tool',
    'tool_call_id': 'call_123',
    'name': 'search',
    'content': 'Python is a high-level programming language...',
    'captured_logs': 'Searching database...\nFound 10 results'
}
verboser.verbose_message(message)
```

## Advanced Features

### Nested Tool Call Display

The `rich_pretty` style automatically displays tool responses nested under their corresponding tool calls:

```
└── ─── 🤖 Assistant ─────────────────────────────────────────────
    Response content here...

    └── ─── ⚡ Tool ─────────────────────────────────────────────
        Tool Call ID: call_123
        Function: search(query="Python")
        Result: Search results...
```

### Markdown Rendering

The `rich_pretty` style automatically detects and renders markdown content:

```python
message = {
    'role': 'assistant',
    'content': '''# Python Overview

Python is a **high-level** programming language.

## Features
- Easy to learn
- Powerful libraries
- Great community
'''
}
verboser.verbose_message(message)
```

### Content Truncation

All styles support automatic content truncation:

```python
verboser = VerboserFactory.get(
    'pretty',
    max_content_length=100,  # Truncate at 100 characters
    max_tool_result_length=200
)
```

## Best Practices

1. **Choose Appropriate Style**:
   - Use `simple` for debugging
   - Use `compact` for minimal output
   - Use `pretty` for standard terminal output
   - Use `rich_pretty` for enhanced visual experience (default)

2. **Configure Length Limits**: Adjust truncation limits based on your terminal size and needs

3. **Use Rich Pretty for Development**: The `rich_pretty` style provides the best visual experience with nested tool calls

4. **Disable Colors When Needed**: Set `show_colors=False` for environments that don't support ANSI colors

5. **Custom Console**: Provide a custom Rich Console instance for advanced formatting control

## Integration with Agent

The verbose system is fully integrated with `DrowAgent`:

```python
from drowcoder import DrowAgent, VerboseStyle

agent = DrowAgent(
    workspace='./project',
    verbose_style=VerboseStyle.RICH_PRETTY  # Default
)

# Messages are automatically displayed using the configured verboser
agent.process("Your instruction here")
```

## Extending the System

To create a custom verboser:

```python
from drowcoder.verbose import BaseMessageVerboser

class CustomVerboser(BaseMessageVerboser):
    def verbose_message(self, message: Dict[str, Any]) -> None:
        # Your custom formatting logic
        role = message.get('role')
        content = message.get('content', '')
        print(f"[{role.upper()}] {content}")

# Use custom verboser
verboser = CustomVerboser()
verboser.verbose_message({'role': 'user', 'content': 'Hello'})
```

## Related Documentation

- See [checkpoint.md](checkpoint.md) for checkpoint system
- See [../tools/base.md](../tools/base.md) for tool architecture

