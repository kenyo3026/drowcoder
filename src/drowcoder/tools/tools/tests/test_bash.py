"""
Unit tests for bash tool.

Tests cover:
- Basic command execution
- Timeout handling
- Working directory control
- Environment variables
- Error handling
- .drowignore validation
- Tool class interface

Usage:
    # Test bash tool
    python -m src.drowcoder.tools.tests.test_bash

    # Test bash tool with module selection
    python -m src.drowcoder.tools.tests.test_bash --module bash
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
import importlib
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Get module name from environment variable or use default
TEST_MODULE = os.environ.get('TEST_BASH_MODULE', 'bash')

# Dynamically import the specified module
bash_module = importlib.import_module(f'drowcoder.tools.{TEST_MODULE}')
CmdResponse = bash_module.CmdResponse
BashTool = bash_module.BashTool

# Helper function to maintain test compatibility
def execute_command(command, cwd=None, timeout_seconds=0, shell=True, env=None,
                   encoding="utf-8", combine_stdout_stderr=True, enable_ignore=True, shell_policy="auto"):
    """Wrapper function for testing - creates tool instance and calls execute"""
    tool = BashTool()
    tool_result = tool.execute(
        cmd=command,
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        shell=shell,
        env=env,
        encoding=encoding,
        combine_stdout_stderr=combine_stdout_stderr,
        enable_ignore=enable_ignore,
        shell_policy=shell_policy,
    )
    # Return CmdResponse for backward compatibility
    if tool_result.success and tool_result.metadata and tool_result.metadata.cmd_response:
        return tool_result.metadata.cmd_response
    else:
        # On error, return a CmdResponse with error information
        # Ensure cwd is a Path object for CmdResponse
        resolved_cwd = Path(cwd).resolve() if cwd else None
        return CmdResponse(
            cmd=command,
            cwd=resolved_cwd,
            exit_code=tool_result.metadata.cmd_response.exit_code if tool_result.metadata and tool_result.metadata.cmd_response else 1,
            output=tool_result.content if tool_result.content else "",
            error=tool_result.error or (tool_result.metadata.cmd_response.error if tool_result.metadata and tool_result.metadata.cmd_response else "Unknown error"),
            pid=tool_result.metadata.cmd_response.pid if tool_result.metadata and tool_result.metadata.cmd_response else None,
            duration_ms=tool_result.metadata.cmd_response.duration_ms if tool_result.metadata and tool_result.metadata.cmd_response else 0,
            timed_out=tool_result.metadata.cmd_response.timed_out if tool_result.metadata and tool_result.metadata.cmd_response else False,
        )


@pytest.fixture
def tmp_path():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestBashBasic:
    """Basic command execution tests."""

    def test_simple_command(self):
        """Test simple command execution."""
        result = execute_command("echo 'Hello World'")

        assert isinstance(result, CmdResponse)
        assert "Hello World" in result.output
        assert result.exit_code == 0

    def test_command_with_exit_code(self):
        """Test command that exits with non-zero code."""
        result = execute_command("exit 42")

        assert result.exit_code == 42

    def test_command_pwd(self, tmp_path):
        """Test command in specific working directory."""
        result = execute_command("pwd", cwd=str(tmp_path))

        assert str(tmp_path) in result.output


class TestBashTimeout:
    """Timeout handling tests."""

    def test_timeout_command(self):
        """Test command that times out."""
        result = execute_command("sleep 5", timeout_seconds=1)

        assert result.timed_out is True

    def test_no_timeout(self):
        """Test command that completes before timeout."""
        result = execute_command("echo 'fast'", timeout_seconds=10)

        assert result.timed_out is False
        assert "fast" in result.output


class TestBashEnvironment:
    """Environment variable tests."""

    def test_with_env_var(self):
        """Test command with custom environment variable."""
        result = execute_command(
            "echo $MY_TEST_VAR",
            env={"MY_TEST_VAR": "test_value"}
        )

        assert "test_value" in result.output

    def test_multiple_env_vars(self):
        """Test command with multiple environment variables."""
        result = execute_command(
            "echo $VAR1 $VAR2",
            env={"VAR1": "hello", "VAR2": "world"}
        )

        assert "hello" in result.output and "world" in result.output


class TestBashWorkingDirectory:
    """Working directory tests."""

    def test_cwd_absolute_path(self, tmp_path):
        """Test with absolute path as cwd."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = execute_command(f"cat {test_file.name}", cwd=str(tmp_path))

        assert "test content" in result.output

    def test_cwd_with_pathlib(self, tmp_path):
        """Test with Path object as cwd."""
        result = execute_command("pwd", cwd=tmp_path)

        assert str(tmp_path) in result.output


class TestBashErrors:
    """Error handling tests."""

    def test_invalid_command(self):
        """Test with invalid command."""
        result = execute_command("this_command_does_not_exist_12345")

        # Non-zero exit code
        assert result.exit_code != 0 or result.error is not None


class TestBashOutputFormats:
    """Output format tests."""

    def test_multiline_output(self):
        """Test command with multiline output."""
        result = execute_command("echo 'line1'; echo 'line2'; echo 'line3'")

        assert "line1" in result.output
        assert "line2" in result.output
        assert "line3" in result.output


class TestBashIgnoreValidation:
    """Test .drowignore validation."""

    def test_ignore_disabled(self):
        """Test with .drowignore validation disabled."""
        result = execute_command("echo 'test'", enable_ignore=False)

        assert "test" in result.output

    def test_ignore_enabled(self):
        """Test with .drowignore validation enabled (default)."""
        result = execute_command("echo 'test'", enable_ignore=True)

        assert "test" in result.output


class TestBashToolClass:
    """Tests for BashTool class interface."""

    def test_tool_initialization(self):
        """Test that tool can be initialized."""
        tool = BashTool()
        assert tool is not None

    def test_tool_execute_returns_result(self):
        """Test that tool.execute() returns result."""
        tool = BashTool()
        result = tool.execute(cmd="echo 'test'")
        assert result is not None

    def test_tool_with_logger(self):
        """Test tool with custom logger."""
        import logging
        logger = logging.getLogger("test_logger")
        tool = BashTool(logger=logger)
        assert tool is not None

    def test_tool_with_callback(self):
        """Test tool with callback function."""
        callback_called = []

        def test_callback(event, data):
            callback_called.append((event, data))

        tool = BashTool(callback=test_callback)
        result = tool.execute(cmd="echo 'test'")
        # Callback might be called
        assert result is not None


class TestBashEdgeCases:
    """Edge case tests."""

    def test_empty_output(self):
        """Test command with no output."""
        result = execute_command("true")

        assert result.exit_code == 0
        assert result.output == "" or result.output.strip() == ""

    def test_large_output(self):
        """Test command with large output."""
        # Generate reasonably large output
        result = execute_command("seq 1 100")

        assert "100" in result.output

    def test_command_with_quotes(self):
        """Test command with quotes."""
        result = execute_command("echo 'hello \"world\"'")

        assert "hello" in result.output and "world" in result.output


class TestBashResultProperties:
    """Test CmdResponse properties."""

    def test_result_has_required_fields(self):
        """Test that result has all required fields."""
        result = execute_command("echo 'test'")

        assert isinstance(result, CmdResponse)
        assert hasattr(result, 'cmd')
        assert hasattr(result, 'exit_code')
        assert hasattr(result, 'output')
        assert hasattr(result, 'duration_ms')
        assert hasattr(result, 'timed_out')
        assert hasattr(result, 'pid')

    def test_result_to_dict(self):
        """Test CmdResponse.to_dict() method."""
        result = execute_command("echo 'test'")

        assert isinstance(result, CmdResponse)
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert 'cmd' in result_dict
        assert 'exit_code' in result_dict

    def test_result_to_pretty_str(self):
        """Test CmdResponse.to_pretty_str() method."""
        result = execute_command("echo 'test'")

        assert isinstance(result, CmdResponse)
        pretty_str = result.to_pretty_str()
        assert isinstance(pretty_str, str)
        assert 'cmd:' in pretty_str
        assert 'exit_code:' in pretty_str


class TestBashParametrized:
    """Parametrized tests for various inputs."""

    @pytest.mark.parametrize("command", [
        "echo 'hello'",
        "pwd",
        "date",
    ])
    def test_various_commands(self, command):
        """Test various simple commands."""
        result = execute_command(command)

        # Should return successfully
        assert result.exit_code == 0

    @pytest.mark.parametrize("timeout", [0, 5, 10])
    def test_various_timeouts(self, timeout):
        """Test various timeout values."""
        result = execute_command("echo 'fast'", timeout_seconds=timeout)

        assert "fast" in result.output
        assert result.timed_out is False


if __name__ == "__main__":
    import argparse
    from .base import run_tests_with_report

    parser = argparse.ArgumentParser()
    parser.add_argument('--module', default='bash',
                        choices=['bash'],
                        help='Which module to test')
    args = parser.parse_args()

    # Set environment variable for the test module
    os.environ['TEST_BASH_MODULE'] = args.module

    # Use module name as tool name
    tool_name = args.module

    print(f"Testing module: {args.module}")
    print(f"Report name: {tool_name}")
    print("=" * 70)

    sys.exit(run_tests_with_report(__file__, tool_name))

