"""
Refactored execute tool using unified tool architecture.

This module provides command execution functionality with:
- Safe shell command execution with timeout protection
- .drowignore file validation for security
- Structured result output with exit codes and timing
- Environment variable and working directory control
- Cross-platform support (Unix/Windows)
- Unified tool interface with BaseTool
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess
import time
import os

from .base import BaseTool, ToolResult
from .utils.ignore import IGNORE_FILENAME, IgnoreController


@dataclass
class CommandConfig:
    """Configuration for executing a command."""
    command: str
    cwd: Optional[Path] = None
    timeout_seconds: int = 0  # 0 means no timeout
    shell: bool = True
    env: Optional[Dict[str, str]] = None
    encoding: str = "utf-8"
    combine_stdout_stderr: bool = True
    enable_ignore: bool = True
    shell_policy: str = "auto"  # "auto" | "unix" | "powershell"


@dataclass
class CommandResult:
    """Result of a command execution."""
    command: str
    cwd: Optional[Path]
    exit_code: Optional[int]
    output: str
    error: Optional[str]
    pid: Optional[int]
    duration_ms: int
    timed_out: bool

    def to_dict(self):
        return asdict(self)

    def to_str(self):
        _dict = self.to_dict()
        return str(_dict)

    def to_pretty_str(self):
        _dict = self.to_dict()
        return '\n'.join([f'{key}: {str(value)}' for key, value in _dict.items()])


@dataclass
class ExecuteToolResult(ToolResult):
    """
    Result from execute tool execution.

    Extends ToolResult with command execution-specific information.
    """
    command_result: Optional[CommandResult] = None


class ExecuteTool(BaseTool):
    """
    Tool for executing shell commands safely.

    Provides timeout protection, .drowignore validation,
    and structured result output.
    """
    name = 'execute_command'

    def __init__(self, **kwargs):
        """Initialize ExecuteTool."""
        super().__init__(**kwargs)

    def execute(
        self,
        command: str,
        cwd: Optional[str | Path] = None,
        timeout_seconds: int = 0,
        shell: bool = True,
        env: Optional[Dict[str, str]] = None,
        encoding: str = "utf-8",
        combine_stdout_stderr: bool = True,
        enable_ignore: bool = True,
        shell_policy: str = "auto",
    ) -> ExecuteToolResult:
        """
        Execute a shell command.

        Args:
            command: The bash/shell command to execute
            cwd: Working directory (defaults to current directory)
            timeout_seconds: Timeout in seconds (0 = no timeout)
            shell: Execute with shell=True
            env: Environment variables (merged with os.environ)
            encoding: Text encoding (default: utf-8)
            combine_stdout_stderr: Combine stderr into stdout
            enable_ignore: Enable .drowignore validation
            shell_policy: Shell parsing policy for .drowignore ("auto", "unix", "powershell")

        Returns:
            ExecuteToolResult with command execution details
        """
        self._validate_initialized()

        try:
            # Create configuration
            config = CommandConfig(
                command=command,
                cwd=Path(cwd).resolve() if cwd else None,
                timeout_seconds=timeout_seconds,
                shell=shell,
                env=env,
                encoding=encoding,
                combine_stdout_stderr=combine_stdout_stderr,
                enable_ignore=enable_ignore,
                shell_policy=shell_policy,
            )

            # Execute command
            cmd_result = self._run_command(config)

            # Trigger callback if configured
            self._trigger_callback("command_executed", {
                "command": command,
                "exit_code": cmd_result.exit_code,
                "duration_ms": cmd_result.duration_ms,
                "timed_out": cmd_result.timed_out
            })

            self.logger.info(f"Command executed: {command} (exit_code={cmd_result.exit_code}, duration={cmd_result.duration_ms}ms)")

            return ExecuteToolResult(
                success=True,
                command_result=cmd_result,
                result=cmd_result.to_pretty_str()
            )

        except Exception as e:
            error_msg = f"Command execution failed: {str(e)}"
            self.logger.error(error_msg)

            return ExecuteToolResult(
                success=False,
                error=error_msg
            )

    def _run_command(self, config: CommandConfig) -> CommandResult:
        """Execute command based on configuration."""

        # Check .drowignore validation
        if config.enable_ignore:
            controller = IgnoreController(config.cwd or Path.cwd(), shell=config.shell_policy)
            controller.load()
            blocked = controller.validate_command(config.command)
            if blocked:
                return CommandResult(
                    command=config.command,
                    cwd=config.cwd,
                    exit_code=1,
                    output="",
                    error=f"Blocked by {IGNORE_FILENAME}: attempted to access '{blocked}'",
                    pid=None,
                    duration_ms=0,
                    timed_out=False,
                )

        start_monotonic = time.monotonic()
        cwd_str = str(config.cwd) if config.cwd else None

        popen_kwargs = dict(
            shell=config.shell,
            cwd=cwd_str,
            env={**os.environ, **(config.env or {})} if config.env else None,
            stdout=subprocess.PIPE,
            stderr=(subprocess.STDOUT if config.combine_stdout_stderr else subprocess.PIPE),
            text=True,
            encoding=config.encoding,
        )

        proc: Optional[subprocess.Popen] = None
        timed_out = False
        output = ""
        error_text: Optional[str] = None
        pid: Optional[int] = None
        exit_code: Optional[int] = None

        try:
            proc = subprocess.Popen(config.command, **popen_kwargs)
            pid = proc.pid

            try:
                stdout, stderr = proc.communicate(timeout=(config.timeout_seconds or None))
            except subprocess.TimeoutExpired:
                timed_out = True
                proc.kill()
                # Drain any remaining output
                stdout, stderr = proc.communicate()

            exit_code = proc.returncode

            if config.combine_stdout_stderr:
                output = stdout or ""
                # In combined mode, stderr is already in stdout
            else:
                # Keep them separate but return both concatenated with a marker
                out_part = stdout or ""
                err_part = stderr or ""
                if err_part:
                    error_text = err_part
                output = out_part

        finally:
            duration_ms = int((time.monotonic() - start_monotonic) * 1000)

        # If timed out, make it explicit in error_text keeping output as-is for context
        if timed_out:
            timeout_msg = f"Command execution timed out after {config.timeout_seconds}s"
            error_text = (error_text + "\n" + timeout_msg) if error_text else timeout_msg

        return CommandResult(
            command=config.command,
            cwd=config.cwd,
            exit_code=exit_code,
            output=output,
            error=error_text,
            pid=pid,
            duration_ms=duration_ms,
            timed_out=timed_out,
        )


# Backward compatible function interface
def execute_command(
    command: str,
    cwd: Optional[str | Path] = None,
    timeout_seconds: int = 0,
    shell: bool = True,
    env: Optional[Dict[str, str]] = None,
    encoding: str = "utf-8",
    combine_stdout_stderr: bool = True,
    enable_ignore: bool = True,
    shell_policy: str = "auto",
) -> CommandResult:
    """
    Execute a bash/shell command and return structured output.

    This is a backward-compatible wrapper around ExecuteTool.
    Preserves the exact interface and behavior of the original function.

    Features:
    - Safe command execution with timeout protection
    - .drowignore file validation for security
    - Structured result with exit code and timing info
    - Cross-platform support

    Args:
        command: The bash command to execute. Can be any valid shell command
        cwd: Working directory (defaults to current directory)
        timeout_seconds: Timeout in seconds (0 = no timeout)
        shell: Execute with shell=True (default: True)
        env: Additional environment variables to merge with os.environ
        encoding: Text encoding for output (default: utf-8)
        combine_stdout_stderr: Combine stderr into stdout (default: True)
        enable_ignore: Enable .drowignore validation (default: True)
        shell_policy: Shell parsing policy for .drowignore validation
                     ("auto", "unix", "powershell", default: "auto")

    Returns:
        CommandResult: Structured result containing:
            - command: The executed command
            - cwd: Working directory
            - exit_code: Exit code (None if process failed to start)
            - output: Combined stdout/stderr or stdout only
            - error: Error message (stderr if separate, timeout info)
            - pid: Process ID
            - duration_ms: Execution time in milliseconds
            - timed_out: Whether the command timed out

    Examples:
        # Basic command execution
        result = execute_command("ls -la")
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")

        # With timeout
        result = execute_command("sleep 10", timeout_seconds=5)
        if result.timed_out:
            print("Command timed out!")

        # With custom working directory
        result = execute_command("pwd", cwd="/tmp")

        # With environment variables
        result = execute_command("echo $MY_VAR", env={"MY_VAR": "hello"})
    """
    tool = ExecuteTool()
    tool_result = tool.execute(
        command=command,
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        shell=shell,
        env=env,
        encoding=encoding,
        combine_stdout_stderr=combine_stdout_stderr,
        enable_ignore=enable_ignore,
        shell_policy=shell_policy,
    )

    # Return CommandResult for backward compatibility
    if tool_result.success and tool_result.command_result:
        return tool_result.command_result
    else:
        # On error, return a CommandResult with error information
        return CommandResult(
            command=command,
            cwd=Path(cwd).resolve() if cwd else None,
            exit_code=1,
            output="",
            error=tool_result.error or "Unknown error",
            pid=None,
            duration_ms=0,
            timed_out=False,
        )

