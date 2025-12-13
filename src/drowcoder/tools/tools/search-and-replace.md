# Search and Replace Tool

## Overview

The `search_and_replace` tool provides file content search and replace functionality with exact line matching, multi-line pattern support, preview/apply modes, and multiple output styles (default, git_diff, git_conflict).

## Features

- **Exact Line Matching**: Single-line and multi-line exact string matching
- **Flexible Replacement**: One-to-many, many-to-one, and deletion operations
- **Preview Mode**: Safe preview of changes before applying
- **Multiple Output Styles**: Default, git diff, and git conflict formats
- **Line Range Targeting**: Optional start/end line constraints
- **Case Sensitivity Control**: Configurable case-sensitive matching

## Parameters

### Required Parameters

- **`file`** (string | Path): Target file or directory path to search in
- **`search`** (string): Exact line(s) to find. Use `'\n'` for consecutive multi-line patterns
- **`replace`** (string | List[str]): Replacement content. Can be multiline string or empty string for deletion

### Optional Parameters

- **`file_pattern`** (string): File pattern to match (default: `"*"`)
- **`case_sensitive`** (bool): Whether search is case sensitive (default: True)
- **`start_line`** (int): Start line number for search range (optional)
- **`end_line`** (int): End line number for search range (optional)
- **`mode`** (string): Execution mode - `"preview"` or `"apply"` (default: `"apply"`)
- **`output_style`** (string): Output style - `"default"`, `"git_diff"`, or `"git_conflict"` (default: `"default"`)
- **`output_file`** (string | Path): Optional output file path (for apply mode)

## Usage Examples

### Single Line Replacement

```python
from drowcoder.tools import SearchAndReplaceTool

tool = SearchAndReplaceTool()

response = tool.execute(
    file="./src/main.py",
    search="import os",
    replace="import os\nimport sys"
)
```

### Multi-Line Replacement

```python
response = tool.execute(
    file="./config.py",
    search="DEBUG = True\nLOG_LEVEL = 'info'",
    replace="DEBUG = False\nLOG_LEVEL = 'debug'"
)
```

### Preview Mode (Safe Testing)

```python
response = tool.execute(
    file="./src/utils.py",
    search="old_function()",
    replace="new_function()",
    mode="preview",
    output_style="git_diff"
)
```

### Case-Insensitive Replacement

```python
response = tool.execute(
    file="./README.md",
    search="Python",
    replace="Python 3.11",
    case_sensitive=False
)
```

### Line Range Replacement

```python
response = tool.execute(
    file="./src/main.py",
    search="TODO",
    replace="DONE",
    start_line=10,
    end_line=50
)
```

### Deletion (Empty Replace)

```python
response = tool.execute(
    file="./config.py",
    search="deprecated_option = True",
    replace=""  # Deletes the matching line
)
```

## Response Format

The tool returns a `SearchAndReplaceToolResponse` with:

- **`success`**: `True` if operation completed successfully
- **`content`**: Summary message or formatted output (depending on mode)
- **`error`**: Error message if operation failed
- **`file_responses`**: List of `FileResponse` objects, each containing:
  - `file_path`: Path to the processed file
  - `matches`: List of `LineMatch` objects with match details
  - `has_matches`: Boolean indicating if matches were found
  - `total_matches`: Number of matches found

## Execution Modes

### Preview Mode

In preview mode (`mode="preview"`), the tool:
- Shows what changes would be made without modifying files
- Outputs formatted content based on `output_style`
- Logs preview information to logger
- Does not write any files

### Apply Mode

In apply mode (`mode="apply"`), the tool:
- Actually modifies files with replacements
- Writes changes to target files
- Can write to different output file if `output_file` specified
- Returns summary of files modified

## Output Styles

### Default Style

Returns complete modified file content:

```python
response = tool.execute(
    file="./src/main.py",
    search="old_code",
    replace="new_code",
    output_style="default"
)
```

### Git Diff Style

Returns git diff format for easy review:

```diff
diff --git a/src/main.py b/src/main.py
@@ -10,1 +10,1 @@
-old_code
+new_code
```

### Git Conflict Style

Returns git conflict markers for VS Code rendering:

```
<<<<<<< HEAD
old_code
=======
new_code
>>>>>>> incoming
```

## Matching Behavior

### Single Line Matching

Matches exact line content (after stripping whitespace):

```python
# Matches: "  import os  " (whitespace is stripped)
search="import os"
```

### Multi-Line Matching

Matches consecutive lines exactly:

```python
# Matches consecutive lines:
search="line1\nline2\nline3"
```

### Case Sensitivity

When `case_sensitive=False`, matching is case-insensitive:

```python
# Matches: "Python", "python", "PYTHON"
search="Python"
case_sensitive=False
```

## Best Practices

1. **Use Preview First**: Always preview changes before applying, especially for bulk replacements
2. **Test on Single File**: Test patterns on a single file before applying to directories
3. **Use Line Ranges**: Narrow down replacements with `start_line` and `end_line` when possible
4. **Check Matches**: Review `file_responses` to verify expected matches were found
5. **Backup Important Files**: Create backups before applying large replacements
6. **Use Git Diff Style**: Use `git_diff` output style for reviewing changes

## Error Handling

The tool handles various error scenarios:

- **File Not Found**: Returns error if target file or directory doesn't exist
- **No Matches**: Returns success with empty `file_responses` list
- **Identical Search/Replace**: Returns success with "No changes needed" message
- **File Read Errors**: Logs warnings for files that can't be read but continues processing

## Implementation Details

- **Exact Matching**: Uses exact string matching (not regex) for precise control
- **Line-by-Line**: Processes files line by line for accurate line number tracking
- **Multi-Line Support**: Handles multi-line patterns by matching consecutive lines
- **Replacement Order**: Applies replacements from bottom to top to maintain line numbers

## Related Documentation

- See [base.md](base.md) for architecture details

