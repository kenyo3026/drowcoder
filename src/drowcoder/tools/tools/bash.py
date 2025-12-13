"""
Refactored bash tool using unified tool architecture.

This module provides command execution functionality with:
- Safe shell command execution with timeout protection
- .drowignore file validation for security
- Structured result output with exit codes and timing
- Environment variable and working directory control
- Cross-platform support (Unix/Windows)
- Unified tool interface with BaseTool
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional, Union
import subprocess
import time
import os

from .base import BaseTool, ToolResponse, ToolResponseMetadata, ToolResponseType, _IntactType
from .utils.ignore import IGNORE_FILENAME, IgnoreController

TOOL_NAME = 'bash_cmd'

@dataclass
class CmdConfig:
    """Configuration for executing a command."""
    cmd: str
    cwd: Optional[Path] = None
    timeout_seconds: int = 0  # 0 means no timeout
    shell: bool = True
    env: Optional[Dict[str, str]] = None
    encoding: str = "utf-8"
    combine_stdout_stderr: bool = True
    enable_ignore: bool = True
    shell_policy: str = "auto"  # "auto" | "unix" | "powershell"


@dataclass
class CmdResponse:
    """Response from a command execution."""
    cmd: str
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
class BashToolResponse(ToolResponse):
    """
    Response from bash tool execution.

    Extends ToolResponse with command execution-specific information.
    """
    tool_name: str = TOOL_NAME

@dataclass
class BashToolResponseMetadata(ToolResponseMetadata):
    """
    Response metadata from bash tool execution.

    Extends ToolResponseMetadata with command execution-specific fields.

    Attributes:
        cmd_response: The detailed command execution response. None if execution failed before command ran.
    """
    cmd_response: Optional[CmdResponse] = None


class BashTool(BaseTool):
    """
    Tool for executing shell commands safely.

    Provides timeout protection, .drowignore validation,
    and structured result output.
    """
    name = TOOL_NAME

    def __init__(self, **kwargs):
        """Initialize BashTool."""
        super().__init__(**kwargs)

    def execute(
        self,
        cmd: str,
        cwd: Optional[str | Path] = None,
        timeout_seconds: int = 0,
        shell: bool = True,
        env: Optional[Dict[str, str]] = None,
        encoding: str = "utf-8",
        combine_stdout_stderr: bool = True,
        enable_ignore: bool = True,
        shell_policy: str = "auto",
        as_type: Union[str, _IntactType] = ToolResponseType.PRETTY_STR,
        filter_empty_fields: bool = True,
        filter_metadata_fields: bool = True,
    ) -> Any:
        """
        Execute a shell command.

        Args:
            cmd: The bash/shell command to execute
            cwd: Working directory (defaults to current directory)
            timeout_seconds: Timeout in seconds (0 = no timeout)
            shell: Bash with shell=True
            env: Environment variables (merged with os.environ)
            encoding: Text encoding (default: utf-8)
            combine_stdout_stderr: Combine stderr into stdout
            enable_ignore: Enable .drowignore validation
            shell_policy: Shell parsing policy for .drowignore ("auto", "unix", "powershell")
            as_type: Output format type for the response
            filter_empty_fields: Whether to filter empty fields in output
            filter_metadata_fields: Whether to filter metadata fields in output

        Returns:
            BashToolResponse (or converted format based on as_type)
        """
        self._validate_initialized()
        dumping_kwargs = self._parse_dump_kwargs(locals())

        cmd_response = None  # Initialize to avoid UnboundLocalError in exception handler

        try:
            # Create configuration
            config = CmdConfig(
                cmd=cmd,
                cwd=Path(cwd).resolve() if cwd else None,
                timeout_seconds=timeout_seconds,
                shell=shell,
                env=env,
                encoding=encoding,
                combine_stdout_stderr=combine_stdout_stderr,
                enable_ignore=enable_ignore,
                shell_policy=shell_policy,
            )

            # Bash command
            cmd_response = self._run_command(config)

            # Trigger callback if configured
            self._trigger_callback("command_executed", {
                "cmd": cmd,
                "exit_code": cmd_response.exit_code,
                "duration_ms": cmd_response.duration_ms,
                "timed_out": cmd_response.timed_out
            })

            self.logger.info(f"Command executed: {cmd} (exit_code={cmd_response.exit_code}, duration={cmd_response.duration_ms}ms)")

            return BashToolResponse(
                success=True,
                content=cmd_response.to_pretty_str(),
                metadata=BashToolResponseMetadata(
                    cmd_response=cmd_response,
                )
            ).dump(**dumping_kwargs)

        except Exception as e:
            error_msg = f"Command execution failed: {str(e)}"
            self.logger.error(error_msg)

            return BashToolResponse(
                success=False,
                error=error_msg,
            ).dump(**dumping_kwargs)

    def _run_command(self, config: CmdConfig) -> CmdResponse:
        """Execute command based on configuration."""

        # Check .drowignore validation
        if config.enable_ignore:
            controller = IgnoreController(config.cwd or Path.cwd(), shell=config.shell_policy)
            controller.load()
            blocked = controller.validate_command(config.cmd)
            if blocked:
                return CmdResponse(
                    cmd=config.cmd,
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
            proc = subprocess.Popen(config.cmd, **popen_kwargs)
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

        return CmdResponse(
            cmd=config.cmd,
            cwd=config.cwd,
            exit_code=exit_code,
            output=output,
            error=error_text,
            pid=pid,
            duration_ms=duration_ms,
            timed_out=timed_out,
        )
