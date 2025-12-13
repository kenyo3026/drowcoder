# Write Tool

## Overview

The `write` tool provides advanced file writing functionality with multiple operations (create, overwrite, append, prepend), preview/apply modes, multiple output styles (default, git_diff, git_conflict), and comprehensive safety validation.

## Features

- **Multiple Operations**: Create, overwrite, append, and prepend modes
- **Preview Mode**: Safe preview of changes before applying
- **Multiple Output Styles**: Default, git diff, and git conflict formats
- **Safety Validation**: Comprehensive checks for potential issues
- **Backup Support**: Automatic backup creation before overwriting
- **Directory Creation**: Automatic parent directory creation
- **Permission Preservation**: Option to preserve file permissions

## Parameters

### Required Parameters

- **`file_path`** (string | Path): Target file path to write to
- **`content`** (string): Content to write to the file

### Optional Parameters

- **`mode`** (string): Execution mode - `"preview"` or `"apply"` (default: `"apply"`)
- **`output_style`** (string): Output style - `"default"`, `"git_diff"`, or `"git_conflict"` (default: `"default"`)
- **`operation`** (string): Write operation type - `"create"`, `"overwrite"`, `"append"`, or `"prepend"` (default: `"overwrite"`)
- **`output_file`** (string | Path): Optional output file path (for apply mode)
- **`encoding`** (string): Text encoding (default: `"utf-8"`)
- **`backup`** (bool): Whether to create backup before overwriting (default: True)
- **`create_dirs`** (bool): Whether to create parent directories if they don't exist (default: True)
- **`preserve_permissions`** (bool): Whether to preserve file permissions (default: True)

## Write Operations

### Create

Creates a new file. Fails if file already exists.

```python
from drowcoder.tools import WriteTool

tool = WriteTool()

response = tool.execute(
    file_path="./new_file.txt",
    content="New file content",
    operation="create"
)
```

### Overwrite

Replaces entire file content (default operation).

```python
response = tool.execute(
    file_path="./existing_file.txt",
    content="New content",
    operation="overwrite"
)
```

### Append

Adds content to the end of the file.

```python
response = tool.execute(
    file_path="./log.txt",
    content="New log entry",
    operation="append"
)
```

### Prepend

Adds content to the beginning of the file.

```python
response = tool.execute(
    file_path="./config.py",
    content="# Updated config\n",
    operation="prepend"
)
```

## Execution Modes

### Preview Mode

Shows what changes would be made without modifying files:

```python
response = tool.execute(
    file_path="./src/main.py",
    content="new content",
    mode="preview",
    output_style="git_diff"
)
```

### Apply Mode

Actually writes changes to files:

```python
response = tool.execute(
    file_path="./src/main.py",
    content="new content",
    mode="apply"
)
```

## Output Styles

### Default Style

Returns complete file content:

```python
response = tool.execute(
    file_path="./file.txt",
    content="content",
    output_style="default"
)
```

### Git Diff Style

Returns git diff format for easy review:

```diff
diff --git a/file.txt b/file.txt
--- a/file.txt
+++ b/file.txt
@@ -1,1 +1,1 @@
-old content
+new content
```

### Git Conflict Style

Returns git conflict markers for VS Code rendering:

```
<<<<<<< HEAD
old content
=======
new content
>>>>>>> incoming
```

## Usage Examples

### Create New File

```python
response = tool.execute(
    file_path="./src/new_module.py",
    content="def hello():\n    print('Hello')\n",
    operation="create",
    mode="apply"
)
```

### Overwrite with Backup

```python
response = tool.execute(
    file_path="./config.yaml",
    content="new config",
    operation="overwrite",
    backup=True,  # Creates backup automatically
    mode="apply"
)
```

### Append to Log File

```python
response = tool.execute(
    file_path="./app.log",
    content="[INFO] Application started\n",
    operation="append",
    mode="apply"
)
```

### Preview Changes

```python
response = tool.execute(
    file_path="./src/main.py",
    content="updated code",
    mode="preview",
    output_style="git_diff"
)
```

## Response Format

The tool returns a `WriteToolResponse` with:

- **`success`**: `True` if write operation completed successfully
- **`content`**: Summary message or formatted output (depending on mode)
- **`error`**: Error message if operation failed
- **`file_responses`**: List of `FileResponse` objects, each containing:
  - `file_path`: Path to the processed file
  - `change`: `FileChange` object with original/new content
  - `success`: Whether the file operation succeeded
  - `error`: Error message if operation failed
  - `backup_path`: Path to backup file (if created)

## Safety Features

### Validation Warnings

The tool provides warnings for:
- Writing outside current directory tree
- CREATE operation on existing file
- Large content size (>1MB)
- Large line count (>10,000 lines)
- Binary content detection (null bytes)
- File permission issues

### Backup Creation

When `backup=True` and overwriting an existing file:
- Automatic backup creation before modification
- Backup files named `{filename}.backup` or `{filename}.backup.{n}`
- Backup path included in response metadata

### Directory Creation

When `create_dirs=True`:
- Automatically creates parent directories if they don't exist
- Ensures file path is writable before attempting write

## Best Practices

1. **Use Preview First**: Always preview changes before applying, especially for important files
2. **Enable Backups**: Keep `backup=True` for overwrite operations
3. **Check Warnings**: Review validation warnings before applying changes
4. **Use Appropriate Operations**: Choose the right operation type for your use case
5. **Handle Large Files**: Be cautious with very large files (>1MB)
6. **Verify Success**: Check `success` and `file_responses` to verify operations

## Error Handling

The tool handles various error scenarios:

- **File Exists (CREATE)**: Returns error if file exists during create operation
- **No Changes**: Returns success with "No changes needed" if content is identical
- **Permission Errors**: Returns error if file/directory is not writable
- **Invalid Operation**: Returns error if operation type is invalid
- **Invalid Mode/Style**: Returns error if mode or output_style is invalid

## Implementation Details

- **Line Ending Normalization**: Automatically normalizes line endings (`\r\n` → `\n`)
- **Content Comparison**: Checks if content is identical before writing (for overwrite)
- **Atomic Operations**: File operations are performed atomically where possible
- **Encoding Support**: Uses UTF-8 encoding by default, configurable
- **Callback Support**: Triggers callback events on write completion

## Related Documentation

- See [base.md](base.md) for architecture details

