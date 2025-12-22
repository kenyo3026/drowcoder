# Configuration Management

## Overview

The `config` module provides configuration file management utilities for drowcoder. It includes tools for editing, displaying, and validating configuration files, as well as platform-aware editor selection.

## Features

- **Configuration File Operations**: Edit, show, validate, and set default configuration files
- **Multiple Format Support**: Supports both YAML (`.yaml`, `.yml`) and JSON (`.json`) configuration files
- **Platform-Aware Editor Selection**: Automatically selects appropriate editor based on platform and environment
- **Configuration Validation**: Validates YAML/JSON syntax and required fields
- **CLI Integration**: Seamless integration with command-line interface

## Configuration Commands

### Edit Command

Opens the configuration file in the default editor.

```bash
drowcoder config edit
drowcoder config edit --config ./custom_config.yaml
```

**Behavior**:
- Checks if config file exists, prompts to create if missing
- Opens file in platform-appropriate editor
- Respects `EDITOR` and `VISUAL` environment variables

### Show Command

Displays the current configuration file content.

```bash
drowcoder config show
drowcoder config show --config ./custom_config.yaml
```

**Output**: Prints the full configuration file content to stdout.

### Validate Command

Validates the configuration file structure and required fields. Supports both YAML and JSON formats.

```bash
drowcoder config validate
drowcoder config validate --config ./custom_config.yaml
drowcoder config validate --config ./custom_config.json
```

**Validation Checks**:
- YAML/JSON syntax validity
- Root must be a dictionary
- `models` section must exist and be a non-empty list
- Each model must have `model` and `api_key` fields

### Set Command

Sets the default configuration file by copying its content to `~/.drowcoder/config.yaml`. Supports both YAML and JSON input files.

```bash
drowcoder config set /path/to/config.yaml
drowcoder config set /path/to/config.json
```

**Behavior**:
- Reads and validates the specified configuration file (YAML or JSON)
- Copies the content to `~/.drowcoder/config.yaml` (always saved as YAML)
- Ensures the default config directory exists
- Provides clear success/error messages

## API Reference

### Platform

Constants for platform identification.

```python
@dataclass(frozen=True)
class Platform:
    WINDOWS: str = 'Windows'
    DARWIN: str = 'Darwin'
    LINUX: str = 'Linux'
```

**Class Methods**:
- `get_default_editor() -> str`: Get platform-specific default editor

### Editor

Constants and utilities for text editor selection.

```python
@dataclass(frozen=True)
class Editor:
    NOTEPAD: str = 'notepad'
    VIM: str = 'vim'
    NANO: str = 'nano'
```

**Class Methods**:
- `get_preferred() -> str`: Get preferred editor based on environment and platform

**Priority Order**:
1. `EDITOR` environment variable (primary)
2. `VISUAL` environment variable (fallback)
3. Platform-specific default

### ConfigCommand

Constants for configuration command types.

```python
@dataclass(frozen=True)
class ConfigCommand:
    EDIT: str = 'edit'
    SHOW: str = 'show'
    VALIDATE: str = 'validate'
    SET: str = 'set'
```

### ConfigMain

Main configuration management class.

#### `edit(config_path: Union[str, Path]) -> int`

Open configuration file in editor.

**Parameters**:
- **`config_path`** (Union[str, Path]): Path to configuration file

**Returns**: Exit code (0 for success, 1 for failure)

**Behavior**:
- Creates config file if it doesn't exist (with user confirmation)
- Opens file in preferred editor
- Returns exit code from editor process

**Example**:
```python
from drowcoder.config import ConfigMain

exit_code = ConfigMain.edit('./config.yaml')
```

#### `show(config_path: Union[str, Path, None] = None) -> int`

Display current configuration file content. If no path is provided, shows the default config at `~/.drowcoder/config.yaml`.

**Parameters**:
- **`config_path`** (Union[str, Path, None]): Path to configuration file (optional, defaults to `~/.drowcoder/config.yaml`)

**Returns**: Exit code (0 for success, 1 for failure)

**Example**:
```python
from drowcoder.config import ConfigMain

exit_code = ConfigMain.show('./config.yaml')
```

#### `set(config_path: Union[str, Path]) -> int`

Set default configuration file by copying content to `~/.drowcoder/config.yaml`. Supports both YAML and JSON input files.

**Parameters**:
- **`config_path`** (Union[str, Path]): Path to configuration file (YAML or JSON)

**Returns**: Exit code (0 for success, 1 for failure)

**Behavior**:
- Validates that the config file exists
- Loads configuration from YAML or JSON file
- Validates configuration structure and required fields
- Copies content to `~/.drowcoder/config.yaml` (always saved as YAML)
- Creates default config directory if it doesn't exist

**Example**:
```python
from drowcoder.config import ConfigMain

# Set default config from YAML file
exit_code = ConfigMain.set('./config.yaml')

# Set default config from JSON file
exit_code = ConfigMain.set('./config.json')
```

#### `validate(config_path: Union[str, Path]) -> int`

Validate configuration file. Supports both YAML and JSON formats.

**Parameters**:
- **`config_path`** (Union[str, Path]): Path to configuration file (YAML or JSON)

**Returns**: Exit code (0 for valid, 1 for invalid)

**Validation Rules**:
- File must exist
- Must be valid YAML or JSON
- Root must be a dictionary
- Must have `models` section
- `models` must be a non-empty list
- Each model must have:
  - `model` field (model identifier)
  - `api_key` field (API key)

**Example**:
```python
from drowcoder.config import ConfigMain

# Validate YAML config
exit_code = ConfigMain.validate('./config.yaml')

# Validate JSON config
exit_code = ConfigMain.validate('./config.json')

if exit_code == 0:
    print("Configuration is valid!")
```

## Editor Selection

### Environment Variables

The editor selection follows Unix conventions:

1. **EDITOR** (primary): Most common environment variable
   ```bash
   export EDITOR=vim
   ```

2. **VISUAL** (fallback): Alternative environment variable
   ```bash
   export VISUAL=nano
   ```

3. **Platform Default**: Falls back to platform-specific default
   - Windows: `notepad`
   - macOS/Darwin: `vim`
   - Linux: `vim`

### Platform Defaults

```python
from drowcoder.config import Platform

# Get default editor for current platform
editor = Platform.get_default_editor()
# Windows: 'notepad'
# macOS/Linux: 'vim'
```

### Preferred Editor

```python
from drowcoder.config import Editor

# Get preferred editor (checks environment variables first)
editor = Editor.get_preferred()
# Checks: EDITOR -> VISUAL -> Platform default
```

## Configuration File Format

Configuration files can be written in either YAML (`.yaml`, `.yml`) or JSON (`.json`) format. Both formats support the same structure and fields.

### Basic Structure (YAML)

```yaml
models:
  - name: model_name
    api_key: YOUR_API_KEY
    model: model_identifier
    temperature: 0
    roles:
      - chatcompletions
      - postcompletions: "task description"
```

### Basic Structure (JSON)

```json
{
  "models": [
    {
      "name": "model_name",
      "api_key": "YOUR_API_KEY",
      "model": "model_identifier",
      "temperature": 0,
      "roles": [
        "chatcompletions",
        "postcompletions: task description"
      ]
    }
  ]
}
```

### Required Fields

- **Root level**: Must be a dictionary
- **`models`**: Must be a non-empty list
- **Each model**:
  - `model`: Model identifier (required)
  - `api_key`: API key (required)

### Optional Fields

- `name`: Model name identifier
- `temperature`: Temperature setting
- `max_tokens`: Maximum tokens
- `system_prompt`: System prompt
- `roles`: List of role assignments

## Usage Examples

### Programmatic Usage

```python
from drowcoder.config import ConfigMain, ConfigCommand

# Edit configuration
ConfigMain.edit('./config.yaml')

# Show configuration
ConfigMain.show('./config.yaml')

# Validate configuration
result = ConfigMain.validate('./config.yaml')
if result == 0:
    print("Valid!")
else:
    print("Invalid configuration")
```

### CLI Usage

```bash
# Edit configuration
drowcoder config edit

# Show configuration (default: ~/.drowcoder/config.yaml)
drowcoder config show

# Show specific config file
drowcoder config show --config ./custom_config.yaml

# Validate configuration
drowcoder config validate

# Set default configuration (copies content to ~/.drowcoder/config.yaml)
drowcoder config set ./config.yaml
drowcoder config set ./config.json

# Use custom config path
drowcoder config edit --config ./custom_config.yaml
```

### Custom Editor

```bash
# Set editor via environment variable
export EDITOR=code  # VS Code
drowcoder config edit

# Or use VISUAL
export VISUAL=nano
drowcoder config edit
```

## Integration with Main Module

The configuration management is integrated into the main CLI:

```python
from drowcoder.config import ConfigMain, ConfigCommand

# In main.py
if args.command == 'config':
    if args.config_action == ConfigCommand.EDIT:
        return ConfigMain.edit(config_path)
    elif args.config_action == ConfigCommand.SHOW:
        return ConfigMain.show(config_path)
    elif args.config_action == ConfigCommand.VALIDATE:
        return ConfigMain.validate(config_path)
```

## Error Handling

### File Not Found

When editing a non-existent file:
- Prompts user to create the file
- Creates file if user confirms
- Returns error code if user declines

### Editor Not Found

If the specified editor is not found:
- Prints error message
- Suggests setting `EDITOR` environment variable
- Returns error code

### Validation Errors

Validation provides clear error messages:
- ❌ Invalid YAML syntax
- ❌ Missing required fields
- ❌ Invalid structure
- ✅ Valid configuration (with model count)

## Best Practices

1. **Use Environment Variables**: Set `EDITOR` or `VISUAL` for consistent editor selection
2. **Validate Before Use**: Always validate configuration before running agent
3. **Version Control**: Consider excluding API keys from version control
4. **Use Descriptive Names**: Use meaningful model names for easy identification
5. **Regular Validation**: Validate configuration after making changes

## Related Documentation

- See [model.md](model.md) for model configuration handling
- See [checkpoint.md](checkpoint.md) for checkpoint system

