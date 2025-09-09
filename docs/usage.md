# drowcoder Usage Guide

This guide shows you how to use drowcoder in different scenarios.

## 🚀 Four Main Usage Methods

### 1. **Package Import** - Python Code Integration

```python
import sys
sys.path.insert(0, 'src')  # For development
import drowcoder

print(f'✅ Package import successful')
print(f'Version: {drowcoder.__version__}')
print(f'Available: {len([x for x in dir(drowcoder) if not x.startswith("_")])} public attributes')
```

**Use Case**: When you want to integrate drowcoder into your Python applications.

---

### 2. **Development Mode** - Local Development

```bash
python -m src.drowcoder.develop --help
python -m src.drowcoder.develop --workspace /path/to/project
```

**Features**:
- ✅ Checkpoints saved to `./checkpoints/` (local project directory)
- ✅ Perfect for development and testing
- ✅ Auto-detects project root via `pyproject.toml`

**Use Case**: When developing drowcoder or testing new features.

---

### 3. **Production Mode** - Installed Package

```bash
python -m src.drowcoder.cli --help
# Or after installation:
drowcoder --help
drowcoder --workspace /path/to/project
```

**Features**:
- ✅ Checkpoints saved to `~/.drowcoder/checkpoints/` (user directory)
- ✅ Clean separation from development environment
- ✅ Standard CLI tool behavior

**Use Case**: When using drowcoder as an installed tool in production.

---

### 4. **Example Script** - Quick Demo

```bash
PYTHONPATH=$PWD/src python examples/basic_usage.py
```

**Features**:
- ✅ Interactive demo of drowcoder capabilities
- ✅ Shows agent creation and tool listing
- ✅ Optional interactive session with develop mode
- ✅ Perfect for first-time users

**Use Case**: When you want to quickly see drowcoder in action.

---

## 🎯 When to Use Each Method

| Method | Scenario | Checkpoint Location | Best For |
|--------|----------|-------------------|----------|
| **Package Import** | Python integration | N/A | Building apps with drowcoder |
| **Development Mode** | Local development | `./checkpoints/` | Contributing, testing |
| **Production Mode** | Installed usage | `~/.drowcoder/checkpoints/` | End users, production |
| **Example Script** | Quick demo | Uses develop mode | Learning, demos |

## 🛠️ Quick Start

1. **First time users**: Run the example script
2. **Developers**: Use development mode
3. **End users**: Install and use production mode
4. **Integrators**: Use package import in your code

That's it! Choose the method that fits your use case and get started with drowcoder.
