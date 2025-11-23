# Checkpoint System

## Overview

The `Checkpoint` class provides a comprehensive checkpoint management system for drowcoder agents. It enables persistent storage of agent state, including configuration, messages, logs, and todos, allowing for session recovery and state tracking.

## Features

- **Multiple Storage Types**: Supports JSON, text, and structured data storage
- **Automatic Directory Management**: Creates and manages checkpoint directories
- **Context-Aware Storage**: Different storage types for different data (dict, list, text)
- **Persistence**: All agent state can be saved and restored
- **Context Manager Support**: Can be used as a context manager for automatic cleanup

## Checkpoint Structure

A checkpoint directory contains the following files:

```
checkpoint_root/
├── info.json          # System and platform information
├── config.json        # Agent configuration
├── logging.log        # Text log file
├── messages.json      # Processed messages (list)
├── raw_messages.json  # Raw messages (list)
└── todos.json         # Todo list (list)
```

## Basic Usage

### Creating a Checkpoint

```python
from drowcoder import Checkpoint

# Create checkpoint with default name (timestamp-based)
checkpoint = Checkpoint()

# Create checkpoint with custom path
checkpoint = Checkpoint(root='./my_checkpoint')

# Create checkpoint without reinitializing if exists
checkpoint = Checkpoint(
    root='./my_checkpoint',
    force_reinit_if_existence=False
)
```

### Using as Context Manager

```python
with Checkpoint(root='./session') as checkpoint:
    checkpoint.punch_info({'custom_field': 'value'})
    checkpoint.punch_log('Session started')
    # Checkpoint is automatically managed
```

## Checkpoint Components

### CheckpointInfo

Stores system and platform information with automatic timestamp.

```python
checkpoint.info.punch({
    'custom_info': 'value',
    'version': '1.0.0'
})
```

**Default Fields**:
- `create_datetime`: Creation timestamp
- Platform information from `platform.uname()`

**Storage**: JSON file (`info.json`)

### CheckpointConfig

Stores agent configuration.

```python
checkpoint.config.punch({
    'model': 'gpt-4',
    'temperature': 0.7
})
```

**Storage**: JSON file (`config.json`)

### CheckpointLogs

Stores text-based log entries.

```python
# Append log entry
checkpoint.punch_log('Processing started')

# Or directly
checkpoint.logs.punch('Another log entry', mode='a')
```

**Storage**: Text file (`logging.log`)

**Modes**:
- `'a'` or `TxtPunchMode.append`: Append to file
- `'w'` or `TxtPunchMode.write`: Overwrite file

### CheckpointMessages

Stores processed messages (list format).

```python
checkpoint.punch_message({
    'role': 'user',
    'content': 'Hello'
})
```

**Storage**: JSON file (`messages.json`)

### CheckpointRawMessages

Stores raw messages (list format).

```python
checkpoint.punch_raw_message({
    'role': 'assistant',
    'content': 'Response'
})
```

**Storage**: JSON file (`raw_messages.json`)

### CheckpointToDosList

Stores todo items (list format).

```python
checkpoint.punch_todos({
    'id': '1',
    'content': 'Task description',
    'status': 'pending'
})
```

**Storage**: JSON file (`todos.json`)

## Base Classes

The checkpoint system uses several base classes for different storage types:

### CheckpointTxtBase

Base class for text file storage.

```python
@dataclass
class CheckpointTxtBase:
    path: str
    context: Optional[str] = None

    def punch(self, context: str, mode: Union[str, TxtPunchMode]='a'):
        # Append or write text to file
```

### CheckpointDictBase

Base class for dictionary storage (JSON).

```python
@dataclass
class CheckpointDictBase:
    path: str
    context: Dict[str, Any] = field(default_factory=dict)

    def punch(self, context: Dict[str, Any]):
        # Update dictionary and save to JSON
```

### CheckpointListBase

Base class for list storage (JSON).

```python
@dataclass
class CheckpointListBase:
    path: str
    context: List[Any] = field(default_factory=list)

    def punch(self, context: Any):
        # Append to list and save to JSON
```

### CheckpointJsonBase

Factory class that creates either `CheckpointDictBase` or `CheckpointListBase` based on context type.

```python
# Automatically creates CheckpointDictBase for dict
checkpoint = CheckpointJsonBase('path.json', {'key': 'value'})

# Automatically creates CheckpointListBase for list
checkpoint = CheckpointJsonBase('path.json', [1, 2, 3])
```

## API Reference

### Checkpoint Class

#### `__init__(root=None, force_reinit_if_existence=True, logger=None)`

Initialize a checkpoint.

**Parameters**:
- **`root`** (str, optional): Checkpoint directory path. If `None`, uses timestamp-based name
- **`force_reinit_if_existence`** (bool): If `True`, removes existing directory before creating (default: `True`)
- **`logger`** (Logger, optional): Logger instance for checkpoint operations

**Attributes**:
- `checkpoint_root` (Path): Path to checkpoint directory
- `info` (CheckpointInfo): System information storage
- `config` (CheckpointConfig): Configuration storage
- `logs` (CheckpointLogs): Log file storage
- `messages` (CheckpointMessages): Processed messages storage
- `raw_messages` (CheckpointRawMessages): Raw messages storage
- `todos` (CheckpointToDosList): Todo list storage

#### `init_checkpoint(root=None, force_reinit_if_existence=True)`

Initialize or reinitialize checkpoint directory.

**Parameters**:
- **`root`** (str, optional): Checkpoint directory path
- **`force_reinit_if_existence`** (bool): Remove existing directory if exists

#### `punch_info(*args, **kwargs)`

Add information to `info.json`.

```python
checkpoint.punch_info({'key': 'value'})
```

#### `punch_log(*args, **kwargs)`

Add log entry to `logging.log`.

```python
checkpoint.punch_log('Log message', mode='a')
```

#### `punch_message(*args, **kwargs)`

Add message to `messages.json`.

```python
checkpoint.punch_message({'role': 'user', 'content': 'Hello'})
```

#### `punch_raw_message(*args, **kwargs)`

Add raw message to `raw_messages.json`.

```python
checkpoint.punch_raw_message({'role': 'assistant', 'content': 'Hi'})
```

#### `punch_todos(*args, **kwargs)`

Add todo item to `todos.json`.

```python
checkpoint.punch_todos({'id': '1', 'content': 'Task', 'status': 'pending'})
```

## Usage Examples

### Basic Checkpoint Creation

```python
from drowcoder import Checkpoint

# Create checkpoint
checkpoint = Checkpoint(root='./my_session')

# Store configuration
checkpoint.punch_config({
    'model': 'gpt-4',
    'temperature': 0.7,
    'max_tokens': 2000
})

# Log events
checkpoint.punch_log('Agent initialized')
checkpoint.punch_log('Processing user request')

# Store messages
checkpoint.punch_message({
    'role': 'user',
    'content': 'What is Python?'
})
```

### Session Recovery

```python
import json
from pathlib import Path
from drowcoder import Checkpoint

# Load existing checkpoint
checkpoint_path = Path('./previous_session')
if checkpoint_path.exists():
    checkpoint = Checkpoint(
        root=str(checkpoint_path),
        force_reinit_if_existence=False
    )

    # Load previous messages
    with open(checkpoint.checkpoint_root / 'messages.json') as f:
        messages = json.load(f)

    # Continue from where we left off
    print(f"Resuming session with {len(messages)} messages")
```

### Context Manager Usage

```python
with Checkpoint(root='./session') as checkpoint:
    checkpoint.punch_info({'session_id': '12345'})
    checkpoint.punch_log('Session started')

    try:
        # Agent operations
        checkpoint.punch_message({'role': 'user', 'content': 'Hello'})
    except Exception as e:
        checkpoint.punch_log(f'Error occurred: {e}')
        raise
```

### Custom Checkpoint Components

```python
from drowcoder.checkpoint import CheckpointJsonBase, CheckpointTxtBase

# Create custom JSON checkpoint
custom_json = CheckpointJsonBase(
    path='./custom.json',
    context={'custom': 'data'}
)
custom_json.punch({'new': 'value'})

# Create custom text checkpoint
custom_txt = CheckpointTxtBase(
    path='./custom.txt',
    context='Initial content'
)
custom_txt.punch('Additional content', mode='a')
```

## Integration with Agent

The checkpoint system is automatically integrated with `DrowAgent`:

```python
from drowcoder import DrowAgent, Checkpoint

# Agent automatically creates and uses checkpoint
agent = DrowAgent(
    checkpoint='./agent_session',
    workspace='./project'
)

# Checkpoint is used internally to store:
# - System messages
# - User/assistant messages
# - Tool calls and responses
# - Configuration
```

## Error Handling

The checkpoint system raises `CheckpointError` for various failure scenarios:

```python
from drowcoder.checkpoint import CheckpointError, Checkpoint

try:
    checkpoint = Checkpoint(root='/invalid/path')
    checkpoint.punch_log('Test')
except CheckpointError as e:
    print(f"Checkpoint error: {e}")
```

## Best Practices

1. **Use Descriptive Paths**: Use meaningful checkpoint directory names for easy identification
2. **Handle Errors**: Wrap checkpoint operations in try-except blocks
3. **Regular Cleanup**: Periodically clean up old checkpoint directories
4. **Context Managers**: Use context managers for automatic resource management
5. **Separate Checkpoints**: Use different checkpoints for different sessions or experiments
6. **Version Control**: Consider excluding checkpoint directories from version control (use `.gitignore`)

## File Format Details

### JSON Files

All JSON files use:
- **Indentation**: 4 spaces
- **Encoding**: UTF-8
- **ASCII**: `ensure_ascii=False` (supports Unicode)

### Text Files

Text files use:
- **Encoding**: UTF-8
- **Mode**: Append (`'a'`) by default, can be overwrite (`'w'`)

## Related Documentation

- See [../tools/base.md](../tools/base.md) for tool architecture

