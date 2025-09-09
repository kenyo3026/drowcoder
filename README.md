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

## 📚 Quick Start

1. **Check Examples**: See [examples/basic_usage.py](examples/basic_usage.py)
2. **Learn Usage**: Read [docs/usage.md](docs/usage.md)
3. **Development Guide**: Check other documentation in the project

## 🏗️ Project Structure

```
drowcoder/
├── src/drowcoder/          # Main package
│   ├── main.py            # Core logic
│   ├── cli.py             # Production CLI
│   ├── develop.py         # Development CLI
│   ├── agent.py           # AI agent core
│   ├── tools/             # Tool collection
│   └── prompts/           # System prompts
├── examples/              # Usage examples
├── docs/                  # Documentation
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
- 📖 **View Documentation**: Browse [docs/](docs/) directory
- 💡 **Check Examples**: See [examples/](examples/) directory
- 🔧 **Development Guide**: Read [docs/usage.md](docs/usage.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
