# Drowcoder

> ⚠️ **Development Status**: This project is currently in early development. Features and APIs may change significantly.

A powerful AI agent tool with rich toolsets and flexible configuration options.

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
from drowcoder import DrowAgent, AgentRole

# Create agent
agent = DrowAgent(role=AgentRole.CODER)

# Initialize
agent.initialize()

# Use agent
response = agent.process("Your instruction")
```

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

### Tools

- **[Base Tool](src/drowcoder/tools/base.md)** - Tool architecture and base classes
- **[Attempt Completion](src/drowcoder/tools/attempt-completion.md)** - Task completion signaling
- **[Execute](src/drowcoder/tools/execute.md)** - Command execution
- **[Load](src/drowcoder/tools/load.md)** - File loading
- **[Search](src/drowcoder/tools/search.md)** - Content searching
- **[Search and Replace](src/drowcoder/tools/search-and-replace.md)** - Text replacement
- **[Todo](src/drowcoder/tools/todo.md)** - Task management
- **[Write](src/drowcoder/tools/write.md)** - File writing

## 🏗️ Project Structure

```
drowcoder/
├── src/drowcoder/          # Main package
│   ├── main.py            # Core logic
│   ├── cli.py             # Production CLI
│   ├── develop.py         # Development CLI
│   ├── debug.py           # Debug mode
│   ├── agent.py           # AI agent core
│   ├── docs/              # Module documentation
│   │   ├── agent.md       # Agent entry script
│   │   ├── checkpoint.md  # Checkpoint system
│   │   ├── config.md      # Configuration management
│   │   ├── main.md        # Entry points
│   │   ├── model.md       # Model dispatcher
│   │   └── verbose.md     # Output formatting
│   ├── tools/             # Tool collection
│   │   ├── *.md           # Individual tool docs
│   │   └── *.py           # Tool implementations
│   └── prompts/           # System prompts
├── docs/                  # User documentation
│   └── usage.md           # Usage guide
├── examples/              # Usage examples
├── configs/               # Configuration files
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
  - [Tools](src/drowcoder/tools/) - Individual tool documentation
- 💡 **Check Examples**: See [examples/](examples/) directory
- 🔧 **Development**: See [Development](#-development) section above

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.
