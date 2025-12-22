# Entry Points

## Overview

The drowcoder package provides multiple entry points for different use cases. All entry points are based on the `Main` class, which provides the core execution logic. Each entry point customizes default configurations and behavior for specific scenarios.

## Architecture

```
Main (base class)
├── CliMain (production)
├── DevMain (development)
└── DebugMain (debugging)
```

All entry points inherit from `Main` and customize:
- Default configuration paths
- Default checkpoint locations
- Execution behavior (for debug mode)

## Main Module

The `main.py` module provides the core `Main` class and `MainArgs` dataclass that all entry points are based on.

### MainArgs

Configuration dataclass for command-line arguments:

```python
@dataclass
class MainArgs:
    query: str = None
    config: str = './config.yaml'
    model: str = None
    interactive: bool = False
    workspace: str = None
    checkpoint: str = None
    checkpoint_root: str = './checkpoints'
    command: str = None
    config_action: str = None
```

### Main Class

Core execution class that provides:

- **Configuration Loading**: Loads YAML or JSON configuration
- **Model Dispatching**: Uses ModelDispatcher for role-based model organization
- **Agent Creation**: Creates and initializes DrowAgent
- **Execution Modes**: Supports headless and interactive modes
- **Post-completion**: Supports post-completion tasks
- **Config Commands**: Handles config edit/show/validate subcommands

### Main.run()

Main execution method that:

1. Parses command-line arguments
2. Handles config subcommands (if any)
3. Loads configuration and dispatches models
4. Creates and initializes agent
5. Runs in headless or interactive mode
6. Handles post-completion tasks

## CLI Entry Point (Production)

**File**: `cli.py`
**Class**: `CliMain`
**Usage**: `drowcoder` (after installation) or `python -m src.drowcoder.cli`

### Features

- **User Directory**: Checkpoints saved to `~/.drowcoder/checkpoints/`
- **User Config**: Configuration at `~/.drowcoder/config.yaml`
- **Auto Setup**: Automatically creates and configures config file if missing
- **Production Ready**: Designed for end users

### Default Paths

- **Config**: `~/.drowcoder/config.yaml`
- **Checkpoint Root**: `~/.drowcoder/checkpoints/`

### Configuration Setup

The CLI entry point includes automatic configuration setup:

```python
def setup_config(yaml_path):
    # Creates config file if missing
    # Prompts for model and API key if invalid
    # Returns config path
```

If the config file is missing or invalid, it will:
1. Prompt for model identifier
2. Prompt for API key
3. Create a valid configuration file

### Usage

```bash
# After installation
drowcoder --workspace ./project

# Or directly
python -m src.drowcoder.cli --workspace ./project
```

## Development Entry Point

**File**: `develop.py`
**Class**: `DevMain`
**Usage**: `python -m src.drowcoder.develop`

### Features

- **Project Directory**: Checkpoints saved to `./checkpoints/` (project root)
- **Project Config**: Configuration at `./configs/config.yaml` (project root)
- **Auto Detection**: Automatically finds project root via `pyproject.toml`
- **Development Focus**: Designed for development and testing

### Default Paths

- **Config**: `{project_root}/configs/config.yaml`
- **Checkpoint Root**: `{project_root}/checkpoints/`

### Project Root Detection

Automatically finds project root by searching for `pyproject.toml`:

```python
def find_project_root() -> Path:
    # Searches up directory tree for pyproject.toml
    # Returns project root or current directory
```

### Usage

```bash
# From project root
python -m src.drowcoder.develop --workspace ./project

# Auto-detects project root
python -m src.drowcoder.develop
```

## Debug Entry Point

**File**: `debug.py`
**Class**: `DebugMain`
**Usage**: `python -m src.drowcoder.debug`

### Features

- **Step-by-Step Execution**: Pauses after each iteration
- **Interactive Control**: User confirmation before continuing
- **Response Inspection**: Option to view response dictionary
- **Debug Logging**: Enhanced logging for debugging
- **Same Defaults as Dev**: Uses DevArgs defaults

### Execution Flow

1. Receives user query
2. Executes one completion step
3. Displays iteration information
4. Waits for user confirmation:
   - `y`: Continue to next iteration
   - `n`: Stop debugging
   - `r`: Show response dictionary
5. Repeats until no tool calls or user stops

### Debug Options

- **Continue (y)**: Proceed to next iteration
- **Stop (n)**: End debug session
- **Show Response (r)**: Display response dictionary in YAML format

### Usage

```bash
# Start debug mode
python -m src.drowcoder.debug --workspace ./project

# With initial query
python -m src.drowcoder.debug --query "Your task here"
```

### Example Session

```
🐛 DrowCoder DEBUG mode started!
Agent will pause after each iteration and wait for your confirmation.

============================================================
🔍 DEBUG Iteration 1
============================================================

[Agent executes one step...]

============================================================
⚠️  Tool calls detected. Agent wants to continue.

[DEBUG] (y)continue / (n)stop / (r)show response: r

============================================================
📋 Response Dict:
============================================================
[YAML output of response dictionary]

[DEBUG] (y)continue / (n)stop / (r)show response: y

[Continues to next iteration...]
```

## Comparison Table

| Feature | CLI (Production) | Develop | Debug |
|---------|-----------------|---------|-------|
| **Checkpoint Location** | `~/.drowcoder/checkpoints/` | `./checkpoints/` | `./checkpoints/` |
| **Config Location** | `~/.drowcoder/config.yaml` | `./configs/config.yaml` | `./configs/config.yaml` |
| **Auto Config Setup** | ✅ Yes | ❌ No | ❌ No |
| **Project Root Detection** | ❌ No | ✅ Yes | ✅ Yes |
| **Step-by-Step Execution** | ❌ No | ❌ No | ✅ Yes |
| **Response Inspection** | ❌ No | ❌ No | ✅ Yes |
| **Use Case** | End users | Developers | Debugging |

## Command-Line Arguments

All entry points support the same arguments (inherited from `MainArgs`):

### Primary Arguments

- **`-q, --query`**: Headless mode - process query directly, otherwise interactive
- **`-c, --config`**: Path to configuration file
- **`-m, --model`**: Model to use (overrides config)
- **`-i, --interactive`**: Force interactive mode
- **`-w, --workspace`**: Workspace directory
- **`--checkpoint`**: Checkpoint directory
- **`--checkpoint_root`**: Checkpoint root directory

### Subcommands

- **`config edit`**: Edit configuration file
- **`config show`**: Show current configuration
- **`config validate`**: Validate configuration file

## Execution Modes

### Headless Mode

Process a single query and exit:

```bash
drowcoder --query "Your task" --workspace ./project
```

### Interactive Mode

Continuous interaction loop:

```bash
drowcoder --workspace ./project
# Or
drowcoder --interactive --workspace ./project
```

### Hybrid Mode

Process initial query, then switch to interactive:

```bash
drowcoder --query "Initial task" --interactive --workspace ./project
```

## Post-Completion Tasks

All entry points (except debug) support post-completion tasks:

```yaml
models:
  - name: model
    roles:
      - chatcompletions
      - postcompletions: "Review changes and create summary"
```

After main completion, the agent automatically:
1. Executes post-completion task
2. Uses post-completion model (if different)
3. Continues in same session

## Best Practices

### For End Users

- Use **CLI entry point** (`drowcoder`)
- Configuration automatically set up
- Checkpoints in user directory

### For Developers

- Use **Develop entry point** (`python -m src.drowcoder.develop`)
- Checkpoints in project directory
- Easy to test and iterate

### For Debugging

- Use **Debug entry point** (`python -m src.drowcoder.debug`)
- Step through execution
- Inspect responses
- Understand agent behavior

## Related Documentation

- See [checkpoint.md](checkpoint.md) for checkpoint system
- See [model.md](model.md) for model configuration
- See [config.md](config.md) for configuration management

