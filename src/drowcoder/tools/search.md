# Search Tool

## Overview

The `search` tool provides powerful file content search functionality with regex pattern matching, file pattern filtering, workspace boundary checking, and multiple output formats (tree graph and text).

## Features

- **Regex Pattern Matching**: Search file contents using standard regex syntax
- **File Pattern Filtering**: Filter files by glob patterns (e.g., `*.py`, `*.txt`)
- **Workspace Boundary Checking**: Prevent unauthorized access outside designated working directory
- **Multiple Output Formats**: Tree graph visualization or traditional text format
- **.drowignore Support**: Respects ignore patterns for file filtering
- **Match Limiting**: Control maximum matches displayed per file

## Parameters

### Required Parameters

- **`path`** (string): The directory path to search recursively, or a specific file path to search. Can be relative or absolute path.
- **`content_pattern`** (string): Regular expression pattern to search for within file contents. Use standard regex syntax (e.g., `"TODO"`, `"import.*os"`, `"def\s+\w+"`).
- **`filepath_pattern`** (string): File name pattern to filter which files to search. Supports glob patterns like `"*.py"`, `"*.txt"`, `"config.*"`, or `"*"` for all files.

### Optional Parameters

- **`cwd`** (string): Working directory (workspace root) for boundary checking. If not provided, uses current working directory. Search will be restricted to this workspace unless explicitly allowed.
- **`max_matches_per_file`** (int): Maximum number of matches to display per file (default: 10)
- **`enable_search_outside`** (bool): Allow searching outside workspace (default: True)
- **`as_text`** (bool): Return formatted text or raw results when `as_graph=False` (default: True)
- **`as_graph`** (bool): Use tree graph format for displaying results, takes precedence over `as_text` (default: True)
- **`only_filename`** (bool): If `True`, only return filename and match count; if `False`, return detailed content (default: False)
- **`enable_ignore`** (bool): Enable .drowignore file filtering (default: True)
- **`shell_policy`** (string): Shell policy for command parsing (`"auto"`, `"unix"`, `"powershell"`, default: `"auto"`)

## Usage Examples

### Basic Content Search

```python
from drowcoder.tools import SearchTool

tool = SearchTool()

response = tool.execute(
    path="./src",
    content_pattern="TODO|FIXME",
    filepath_pattern="*.py"
)
```

### Search with Tree Graph Output

```python
response = tool.execute(
    path="./project",
    content_pattern="def\s+\w+",
    filepath_pattern="*.py",
    as_graph=True,
    only_filename=False
)
```

### Quick Filename-Only Search

```python
response = tool.execute(
    path="./src",
    content_pattern=".*",
    filepath_pattern="*.py",
    only_filename=True  # Fast overview without detailed content
)
```

### Search Single File

```python
response = tool.execute(
    path="./src/main.py",
    content_pattern="import",
    filepath_pattern="*"
)
```

## Response Format

The tool returns a `SearchToolResponse` with:

- **`success`**: `True` if search completed successfully
- **`content`**: Formatted search results (tree graph or text format)
- **`error`**: Error message if search failed
- **`metadata`**: `SearchToolResponseMetadata` containing:
  - `path`: The search path
  - `content_pattern`: The regex pattern used
  - `filepath_pattern`: The file pattern used
  - `files_found`: Number of files that matched the search
  - `total_matches`: Total number of matches across all files

## Output Formats

### Tree Graph Format (Default)

Displays results in a hierarchical tree structure showing file paths and matches:

```
project/
    src/
        main.py
          1   | import os
          5   | import sys
        utils.py
          10  | def helper():
```

### Text Format

Traditional list format with file paths and match details:

```
Found 2 files with matches

# src/main.py (2 matches)
  1   | import os
  5   | import sys

# src/utils.py (1 match)
  10  | def helper():
```

## Security Features

### Workspace Boundary Checking

When `enable_search_outside=False`, the tool prevents searching outside the specified workspace directory. This helps prevent unauthorized access to system files or other projects.

### .drowignore Support

Files matching patterns in `.drowignore` are automatically excluded from search results when `enable_ignore=True`.

## Best Practices

1. **Use Specific Patterns**: Narrow down searches with specific regex patterns to avoid overwhelming results
2. **Start with Filename-Only**: Use `only_filename=True` for initial exploration, then get details
3. **Set Match Limits**: Use `max_matches_per_file` to control output size
4. **Respect Workspace**: Keep `enable_search_outside=False` unless necessary
5. **Use File Patterns**: Combine content patterns with file patterns for efficient searching

## Error Handling

The tool handles various error scenarios:

- **Invalid Regex**: Raises `re.error` for invalid regex patterns
- **Path Not Found**: Returns error if search path doesn't exist
- **Outside Workspace**: Returns error if path is outside workspace and `enable_search_outside=False`
- **File Read Errors**: Logs warnings for files that can't be read but continues searching

## Related Documentation

- See [base.md](base.md) for architecture details

