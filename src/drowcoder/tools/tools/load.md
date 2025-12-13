# Load Tool

## Overview

The `load` tool provides file loading functionality for reading file content as plain text. It supports various path formats and provides detailed metadata about loaded files.

## Features

- **Flexible Path Support**: Handles absolute, relative, home directory, and environment variable paths
- **Path Resolution**: Automatic path expansion and resolution
- **Metadata Tracking**: Returns file path and size information
- **Error Handling**: Clear error messages for missing or inaccessible files

## Parameters

### Required Parameters

- **`file_path`** (string): The path to the file to be loaded. Supports:
  - Absolute paths: `/Users/username/file.txt`
  - Relative paths: `./file.txt`, `../file.txt`
  - Home directory: `~/file.txt`
  - Environment variables: `$HOME/file.txt`

### Optional Parameters

- **`ensure_abs`** (bool): Whether to resolve path to absolute form (default: True)
- **`as_type`**: Output format type (default: `PRETTY_STR`)
- **`filter_empty_fields`** (bool): Filter empty fields in output (default: True)
- **`filter_metadata_fields`** (bool): Filter metadata fields in output (default: False)

## Usage Examples

### Load File with Absolute Path

```python
from drowcoder.tools import LoadTool

tool = LoadTool()

response = tool.execute(
    file_path="/Users/username/project/config.yaml"
)
```

### Load File with Relative Path

```python
response = tool.execute(
    file_path="./src/main.py",
    ensure_abs=True
)
```

### Load File with Home Directory

```python
response = tool.execute(
    file_path="~/Documents/notes.txt"
)
```

### Load File with Environment Variable

```python
response = tool.execute(
    file_path="$HOME/project/README.md"
)
```

## Response Format

The tool returns a `LoadToolResponse` with:

- **`success`**: `True` if file was loaded successfully
- **`content`**: The file content as a string
- **`error`**: Error message if loading failed
- **`metadata`**: `LoadToolResponseMetadata` containing:
  - `file_path`: The resolved absolute file path
  - `file_size`: Size of the loaded file in bytes

## Error Handling

The tool handles various error scenarios:

- **File Not Found**: Returns `success=False` with error message "Error: File '{file_path}' not found."
- **Permission Errors**: Returns error message describing the access issue
- **Invalid Path**: Returns error if path cannot be resolved

## Best Practices

1. **Use Absolute Paths**: When possible, use absolute paths or set `ensure_abs=True`
2. **Check Success**: Always verify `success` field before using `content`
3. **Handle Errors**: Check for error messages when `success=False`
4. **File Size**: Use `metadata.file_size` to check file size before processing large files

## Implementation Details

- **Encoding**: Files are read with UTF-8 encoding
- **Path Resolution**: Paths are resolved to absolute form by default
- **File Size**: Calculated using `stat().st_size` for accurate byte count
- **Callback Support**: Triggers a "file_loaded" callback event if configured

## Related Documentation

- See [base.md](base.md) for architecture details

