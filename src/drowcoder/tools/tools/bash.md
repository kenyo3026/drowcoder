# Bash Tool

## Overview

The `bash` tool provides safe shell command execution with timeout protection, ignore file validation, and structured result output. It's designed for running tests, building projects, checking system status, or any shell operations.

## Features

- **Safe Execution**: Timeout protection and .drowignore file validation
- **Structured Output**: Returns exit codes, execution time, and formatted output
- **Cross-Platform**: Supports Unix and Windows systems
- **Environment Control**: Custom environment variables and working directory support
- **Error Handling**: Comprehensive error reporting with timeout detection

## Parameters

### Required Parameters

- **`cmd`** (string): The bash/shell command to execute. Can be any valid shell command including:
  - File operations (ls, cp, mv, rm)
  - Build commands (npm install, pip install, make)
  - Test commands (pytest, npm test, go test)
  - System commands (ps, df, top)
  - Git operations (git status, git commit)

### Optional Parameters

- **`cwd`** (string | Path): Working directory for command execution (defaults to current directory)
- **`timeout_seconds`** (int): Timeout in seconds (0 = no timeout, default: 0)
- **`shell`** (bool): Execute with shell=True (default: True)
- **`env`** (dict): Environment variables to merge with os.environ
- **`encoding`** (string): Text encoding (default: "utf-8")
- **`combine_stdout_stderr`** (bool): Combine stderr into stdout (default: True)
- **`enable_ignore`** (bool): Enable .drowignore validation (default: True)
- **`shell_policy`** (string): Shell parsing policy for .drowignore ("auto", "unix", "powershell", default: "auto")

## Usage Examples

### Basic Command Execution

```python
from drowcoder.tools import BashTool

tool = BashTool()

response = tool.execute(
    cmd="ls -la",
    cwd="/path/to/directory"
)
```

### Command with Timeout

```python
response = tool.execute(
    cmd="npm test",
    timeout_seconds=300,  # 5 minute timeout
    cwd="./project"
)
```

### Command with Custom Environment

```python
response = tool.execute(
    cmd="python script.py",
    env={"PYTHONPATH": "/custom/path", "DEBUG": "1"}
)
```

## Response Format

The tool returns a `ToolResponse` with:

- **`success`**: `True` if command executed (regardless of exit code)
- **`content`**: Formatted string with command execution details
- **`error`**: Error message if execution failed
- **`metadata.cmd_response`**: Detailed `CmdResponse` object containing:
  - `cmd`: The executed command
  - `cwd`: Working directory
  - `exit_code`: Process exit code (None if failed before execution)
  - `output`: Combined stdout/stderr output
  - `error`: Error text (if any)
  - `pid`: Process ID
  - `duration_ms`: Execution time in milliseconds
  - `timed_out`: Whether command timed out

## Security Features

### .drowignore Validation

When `enable_ignore=True`, the tool validates commands against `.drowignore` patterns to prevent unauthorized file access. Commands attempting to access blocked paths will be rejected with exit code 1.

### Timeout Protection

Commands can be limited by execution time to prevent hanging processes. When a timeout occurs:
- Process is killed
- `timed_out` flag is set to `True`
- Error message includes timeout information

## Error Handling

The tool handles various error scenarios:

- **Command Blocked**: Returns exit code 1 with error message
- **Timeout**: Kills process and reports timeout
- **Execution Failure**: Captures error output and exit code
- **Invalid Path**: Returns error if working directory doesn't exist

## Best Practices

1. **Always Set Timeouts**: For potentially long-running commands, set appropriate timeouts
2. **Use .drowignore**: Keep `enable_ignore=True` for security
3. **Check Exit Codes**: Verify `exit_code` in response metadata, not just `success`
4. **Handle Timeouts**: Check `timed_out` flag for timeout scenarios
5. **Specify Working Directory**: Use `cwd` parameter for commands that need specific directory context

## Related Documentation

- See [base.md](base.md) for architecture details

