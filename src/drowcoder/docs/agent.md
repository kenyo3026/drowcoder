# Agent Entry Script

## Overview

The `agent.py` script provides a simple entry point for running drowcoder agents directly. It's a lightweight wrapper around `DrowAgent` that handles basic configuration loading and provides an interactive loop for agent interaction.

## Features

- **Simple Entry Point**: Quick way to start an agent without full CLI setup
- **Configuration Loading**: Loads configuration from YAML or JSON file
- **Interactive Loop**: Continuous interaction loop for agent conversations
- **Basic Argument Parsing**: Command-line arguments for config, workspace, and checkpoint

## Usage

### Basic Usage

```bash
# Run with default configuration
python src/agent.py

# Specify custom configuration
python src/agent.py --config ./configs/config.yaml

# Specify workspace
python src/agent.py --workspace ./my_project

# Specify checkpoint
python src/agent.py --checkpoint ./my_checkpoint
```

### Command-Line Arguments

- **`-c, --config`**: Path to configuration file (default: `../configs/config.yaml`)
- **`-w, --workspace`**: Workspace directory path (optional)
- **`--checkpoint`**: Checkpoint directory path (optional, auto-generated if not provided)

## Code Structure

```python
import argparse
import litellm
from config_morpher import ConfigMorpher

from drowcoder.agent import DrowAgent
from drowcoder.checkpoint import CHECKPOINT_DEFAULT_NAME

if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default='../configs/config.yaml')
    parser.add_argument("-w", "--workspace", default=None, type=str)
    parser.add_argument("--checkpoint", default=None)
    args = parser.parse_args()

    # Load configuration
    config_morpher = ConfigMorpher.from_yaml(args.config)

    # Prepare completion kwargs
    completion_kwargs = config_morpher.morph(
        litellm.completion,
        start_from='models.[name=claude-4-sonnet]'
    )

    # Get tools from config
    tools = config_morpher.fetch('tools', None)

    # Create agent
    agent = DrowAgent(
        workspace=args.workspace,
        tools=tools,
        checkpoint=args.checkpoint or f'../checkpoints/{CHECKPOINT_DEFAULT_NAME()}',
        verbose_style='pretty',
        **completion_kwargs,
    )

    # Initialize and run interactive loop
    agent.init()
    while True:
        agent.receive()
        agent.complete()
```

## Configuration

The script expects a YAML or JSON configuration file with the following structure:

```yaml
models:
  - name: claude-4-sonnet
    api_key: YOUR_API_KEY
    model: anthropic/claude-sonnet-4-20250514
    temperature: 0
    roles:
      - chatcompletions

tools:
  # Tool configurations (optional)
```

## Workflow

1. **Parse Arguments**: Reads command-line arguments for config, workspace, and checkpoint
2. **Load Configuration**: Loads YAML or JSON configuration file using ConfigMorpher
3. **Prepare Completion**: Morphs configuration for LiteLLM completion
4. **Create Agent**: Initializes DrowAgent with configuration
5. **Interactive Loop**: Continuously receives user input and completes agent responses

## Differences from Main Module

This script is simpler than the main CLI module (`src/drowcoder/main.py`):

| Feature | agent.py | main.py |
|---------|----------|---------|
| **Complexity** | Simple | Full-featured |
| **CLI Options** | Basic | Comprehensive |
| **Config Commands** | No | Yes (edit/show/validate) |
| **Interactive Mode** | Always | Optional |
| **Post-completion** | No | Yes |
| **Model Selection** | Hardcoded | Flexible |

## Use Cases

### Development and Testing

Quick way to test agent functionality during development:

```bash
python src/agent.py --config ./test_config.yaml
```

### Simple Interactive Sessions

For simple interactive agent sessions without full CLI features:

```bash
python src/agent.py --workspace ./project
```

### Custom Scripts

Can be used as a base for custom agent scripts:

```python
# Custom agent script based on agent.py
from drowcoder.agent import DrowAgent
from config_morpher import ConfigMorpher

config = ConfigMorpher.from_yaml('config.yaml')
completion_kwargs = config.morph(litellm.completion, start_from='models[0]')

agent = DrowAgent(
    workspace='./project',
    **completion_kwargs
)
agent.init()
# Custom logic here
```

## Limitations

- **Hardcoded Model Selection**: Uses `models.[name=claude-4-sonnet]` - not configurable via CLI
- **No Config Management**: Doesn't support config edit/show/validate commands
- **Always Interactive**: Always runs in interactive loop mode
- **No Post-completion**: Doesn't support post-completion tasks
- **Fixed Verbose Style**: Uses `'pretty'` style (not configurable)

## When to Use

**Use `agent.py` when**:
- You need a quick, simple way to start an agent
- You're developing or testing
- You don't need advanced CLI features
- You want a minimal entry point

**Use `main.py` (via CLI) when**:
- You need full CLI features
- You want config management commands
- You need flexible model selection
- You want post-completion support
- You need production-ready features

## Related Documentation

- See [checkpoint.md](checkpoint.md) for checkpoint system
- See [model.md](model.md) for model configuration
- See [config.md](config.md) for configuration management
- See [verbose.md](verbose.md) for output formatting

