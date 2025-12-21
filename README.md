# Drowcoder

> ⚠️ **Development Status**: This project is currently in early development. Features and APIs may change significantly.

An agentic AI coding assistant framework designed for Cursor IDE, featuring a unified tool dispatcher architecture with built-in tools and MCP (Model Context Protocol) integration.

## ✨ Key Features

- **🔧 Rich Built-in Tools**: 7 essential coding tools (load, search, search_and_replace, write, bash, todo, attempt_completion)
- **🌐 MCP Integration**: Support for both Streamable HTTP and Stdio transports
- **🔀 Unified Dispatcher**: Seamless integration of built-in tools and MCP servers
- **📦 Extensible**: Easy to add custom tools by extending `BaseTool`
- **💾 Checkpoint System**: Persistent state management across sessions
- **⚙️ Flexible Configuration**: YAML-based configuration with role-based model management
- **🚀 Multiple Entry Points**: CLI, development mode, and library usage

## 🚀 Installation

### Method 1: Development Mode Installation (Recommended)

Perfect for development and testing:

```bash
# Clone the repository
git clone https://github.com/kenyo3026/drowcoder.git
cd drowcoder

# Install as editable package (CLI tool will be automatically available)
pip install -e .

# Verify installation
drowcoder --help
```

### Method 2: Direct Git Installation

```bash
pip install git+https://github.com/kenyo3026/drowcoder.git
```

### Method 3: Local Development

If you want to use without installation:

```bash
git clone https://github.com/kenyo3026/drowcoder.git
cd drowcoder

# Development mode
python -m src.drowcoder.develop --help

# Or use examples
python examples/basic_usage.py
```

## 🎯 Usage

### CLI Tool (After Installation)

```bash
# Basic usage
drowcoder --help

# Specify workspace
drowcoder --workspace /path/to/your/project

# Use specific configuration
drowcoder --config /path/to/config.yaml
```

### Library Usage

```python
from drowcoder import DrowAgent

# Create agent with configuration
agent = DrowAgent(
    workspace="/path/to/project",
    tools=None,  # Use default built-in tools
    mcps=None,   # Optional: MCP server configs
    model="gpt-4",
    api_key="your-api-key"
)

# Initialize agent
agent.init()

# Process user query
agent.receive("Your instruction")
agent.complete()
```

> **Note**: For detailed API usage, see [examples/basic_usage.py](examples/basic_usage.py)

## 📚 Documentation

### Quick Start

1. **Check Examples**: See [examples/basic_usage.py](examples/basic_usage.py)
2. **Learn Usage**: Read [docs/usage.md](docs/usage.md) - User guide for getting started
3. **Explore Tools**: Browse tool documentation in [src/drowcoder/tools/](src/drowcoder/tools/)

### Core Modules

- **[Entry Points](src/drowcoder/docs/main.md)** - CLI entry points (main, cli, develop, debug)
- **[Agent](src/drowcoder/docs/agent.md)** - Agent entry script
- **[Checkpoint](src/drowcoder/docs/checkpoint.md)** - Checkpoint system for state management
- **[Config](src/drowcoder/docs/config.md)** - Configuration file management
- **[Model](src/drowcoder/docs/model.md)** - Model dispatcher and role management
- **[Verbose](src/drowcoder/docs/verbose.md)** - Message output formatting system

### Tools & Architecture

- **[Tool Dispatcher Architecture](src/drowcoder/tools/README.md)** - Unified dispatcher system overview
- **[Base Tool](src/drowcoder/tools/tools/base.md)** - Tool architecture and base classes
- **Built-in Tools**:
  - **[Load](src/drowcoder/tools/tools/load.md)** - File loading
  - **[Search](src/drowcoder/tools/tools/search.md)** - Content searching
  - **[Search and Replace](src/drowcoder/tools/tools/search-and-replace.md)** - Text replacement
  - **[Write](src/drowcoder/tools/tools/write.md)** - File writing
  - **[Bash](src/drowcoder/tools/tools/bash.md)** - Command execution
  - **[Todo](src/drowcoder/tools/tools/todo.md)** - Task management
  - **[Attempt Completion](src/drowcoder/tools/tools/attempt-completion.md)** - Task completion signaling
- **[MCP Integration](src/drowcoder/tools/mcps/README.md)** - Model Context Protocol support

## 🏗️ Project Structure

```
drowcoder/
├── src/drowcoder/          # Main package
│   ├── main.py            # Core logic
│   ├── cli.py             # Production CLI
│   ├── develop.py         # Development CLI
│   ├── debug.py           # Debug mode
│   ├── agent.py           # AI agent core
│   ├── checkpoint.py      # Checkpoint management
│   ├── config.py          # Configuration loader
│   ├── model.py           # Model dispatcher
│   ├── verbose.py         # Output formatting
│   ├── docs/              # Module documentation
│   │   ├── main.md        # Entry points
│   │   ├── agent.md       # Agent system
│   │   ├── checkpoint.md  # Checkpoint system
│   │   ├── config.md      # Configuration
│   │   ├── model.md       # Model dispatcher
│   │   └── verbose.md     # Output formatting
│   ├── tools/             # Tool system
│   │   ├── README.md      # Tool architecture overview
│   │   ├── dispatcher.py  # Unified dispatcher
│   │   ├── runtime.py     # Tool runtime
│   │   ├── tools/         # Built-in tools
│   │   │   ├── base.py    # Base tool class
│   │   │   ├── dispatcher.py  # Tool dispatcher
│   │   │   ├── *.py       # Tool implementations
│   │   │   ├── *.yaml     # Tool configurations
│   │   │   ├── *.md       # Tool documentation
│   │   │   ├── tests/     # Tool tests
│   │   │   └── utils/     # Tool utilities
│   │   └── mcps/          # MCP integration
│   │       ├── README.md  # MCP documentation
│   │       ├── base.py    # MCP base client
│   │       ├── dispatcher.py  # MCP dispatcher
│   │       ├── streamable_http.py  # HTTP transport
│   │       ├── stdio.py   # Stdio transport
│   │       └── utils.py   # MCP utilities
│   ├── prompts/           # System prompts
│   │   └── system.py      # System prompt templates
│   └── utils/             # Utilities
│       ├── logger.py      # Logging utilities
│       ├── mixin.py       # Mixin classes
│       └── unique_id.py   # ID generation
├── docs/                  # User documentation
│   └── usage.md           # Usage guide
├── examples/              # Usage examples
│   └── basic_usage.py     # Basic example
├── scripts/               # Utility scripts
├── checkpoints/           # Checkpoints (development)
└── pyproject.toml         # Package configuration
```

## 🔧 Development

### Development Environment Setup

```bash
# Clone and enter project
git clone https://github.com/kenyo3026/drowcoder.git
cd drowcoder

# Install development dependencies
pip install -e .

# Run in development mode
python -m src.drowcoder.develop
```

### Different Execution Methods

| Method | Command | Checkpoint Location | Purpose |
|--------|---------|-------------------|---------|
| **CLI Tool** | `drowcoder` | `~/.drowcoder/checkpoints/` | Production use |
| **Development Mode** | `python -m src.drowcoder.develop` | `./checkpoints/` | Development testing |
| **Package Import** | `from drowcoder import DrowAgent` | Custom | Library usage |
| **Example Script** | `python examples/basic_usage.py` | `./checkpoints/` | Learning reference |

## 💡 Need Help?

- 🐛 **Report Issues**: [GitHub Issues](https://github.com/kenyo3026/drowcoder/issues)
- 📖 **Documentation**:
  - [User Guide](docs/usage.md) - Getting started and usage guide
  - [Core Modules](src/drowcoder/docs/) - Technical documentation for core modules
  - [Tool Dispatcher Architecture](src/drowcoder/tools/README.md) - Unified tool system overview
  - [Built-in Tools](src/drowcoder/tools/tools/) - Individual tool documentation
  - [MCP Integration](src/drowcoder/tools/mcps/README.md) - MCP server integration guide
- 💡 **Check Examples**: See [examples/](examples/) directory
- 🔧 **Development**: See [Development](#-development) section above

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.
