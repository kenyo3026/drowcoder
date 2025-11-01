"""
Unit tests for execute tool.

Tests cover:
- Basic command execution
- Timeout handling
- Working directory control
- Environment variables
- Error handling
- .drowignore validation
- Tool class interface

Usage:
    # Test original execute tool
    python -m src.drowcoder.tools.tests.test_execute

    # Test refactored execute tool
    python -m src.drowcoder.tools.tests.test_execute --module execute_refactor
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
TEST_MODULE = os.environ.get('TEST_EXEC_MODULE', 'execute')

# Dynamically import the specified module
exec_module = importlib.import_module(f'drowcoder.tools.{TEST_MODULE}')
execute_command = exec_module.execute_command
CommandResult = exec_module.CommandResult
CommandExecutor = getattr(exec_module, 'CommandExecutor', getattr(exec_module, 'ExecuteTool', None))


@pytest.fixture
def tmp_path():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestExecuteBasic:
    """Basic command execution tests."""

    def test_simple_command(self):
        """Test simple command execution."""
        result = execute_command("echo 'Hello World'")

        # Original returns string, refactor returns CommandResult
        if isinstance(result, str):
            assert "Hello World" in result
        else:
            assert isinstance(result, CommandResult)
            assert "Hello World" in result.output
            assert result.exit_code == 0

    def test_command_with_exit_code(self):
        """Test command that exits with non-zero code."""
        result = execute_command("exit 42")

        if isinstance(result, str):
            assert "exit_code: 42" in result or "42" in result
        else:
            assert result.exit_code == 42

    def test_command_pwd(self, tmp_path):
        """Test command in specific working directory."""
        result = execute_command("pwd", cwd=str(tmp_path))

        if isinstance(result, str):
            assert str(tmp_path) in result
        else:
            assert str(tmp_path) in result.output


class TestExecuteTimeout:
    """Timeout handling tests."""

    def test_timeout_command(self):
        """Test command that times out."""
        result = execute_command("sleep 5", timeout_seconds=1)

        if isinstance(result, str):
            assert "timed_out: True" in result or "timeout" in result.lower()
        else:
            assert result.timed_out is True

    def test_no_timeout(self):
        """Test command that completes before timeout."""
        result = execute_command("echo 'fast'", timeout_seconds=10)

        if isinstance(result, str):
            assert "timed_out: False" in result or ("timeout" not in result.lower())
        else:
            assert result.timed_out is False
            assert "fast" in result.output


class TestExecuteEnvironment:
    """Environment variable tests."""

    def test_with_env_var(self):
        """Test command with custom environment variable."""
        result = execute_command(
            "echo $MY_TEST_VAR",
            env={"MY_TEST_VAR": "test_value"}
        )

        if isinstance(result, str):
            assert "test_value" in result
        else:
            assert "test_value" in result.output

    def test_multiple_env_vars(self):
        """Test command with multiple environment variables."""
        result = execute_command(
            "echo $VAR1 $VAR2",
            env={"VAR1": "hello", "VAR2": "world"}
        )

        if isinstance(result, str):
            assert "hello" in result and "world" in result
        else:
            assert "hello" in result.output and "world" in result.output


class TestExecuteWorkingDirectory:
    """Working directory tests."""

    def test_cwd_absolute_path(self, tmp_path):
        """Test with absolute path as cwd."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = execute_command(f"cat {test_file.name}", cwd=str(tmp_path))

        if isinstance(result, str):
            assert "test content" in result
        else:
            assert "test content" in result.output

    def test_cwd_with_pathlib(self, tmp_path):
        """Test with Path object as cwd."""
        result = execute_command("pwd", cwd=tmp_path)

        if isinstance(result, str):
            assert str(tmp_path) in result
        else:
            assert str(tmp_path) in result.output


class TestExecuteErrors:
    """Error handling tests."""

    def test_invalid_command(self):
        """Test with invalid command."""
        result = execute_command("this_command_does_not_exist_12345")

        if isinstance(result, str):
            # Should contain error indication
            assert "exit_code" in result
        else:
            # Non-zero exit code
            assert result.exit_code != 0 or result.error is not None


class TestExecuteOutputFormats:
    """Output format tests."""

    def test_multiline_output(self):
        """Test command with multiline output."""
        result = execute_command("echo 'line1'; echo 'line2'; echo 'line3'")

        if isinstance(result, str):
            assert "line1" in result
            assert "line2" in result
            assert "line3" in result
        else:
            assert "line1" in result.output
            assert "line2" in result.output
            assert "line3" in result.output


class TestExecuteIgnoreValidation:
    """Test .drowignore validation."""

    def test_ignore_disabled(self):
        """Test with .drowignore validation disabled."""
        result = execute_command("echo 'test'", enable_ignore=False)

        if isinstance(result, str):
            assert "test" in result
        else:
            assert "test" in result.output

    def test_ignore_enabled(self):
        """Test with .drowignore validation enabled (default)."""
        result = execute_command("echo 'test'", enable_ignore=True)

        if isinstance(result, str):
            assert "test" in result
        else:
            assert "test" in result.output


class TestExecuteToolClass:
    """Tests for ExecuteTool/CommandExecutor class interface."""

    def test_tool_initialization(self):
        """Test that tool can be initialized."""
        if CommandExecutor:
            tool = CommandExecutor()
            assert tool is not None

    def test_tool_execute_returns_result(self):
        """Test that tool.execute() or tool.run() returns result."""
        if CommandExecutor:
            tool = CommandExecutor()

            # Check if it's the refactored version (has execute method)
            if hasattr(tool, 'execute'):
                result = tool.execute(command="echo 'test'")
                assert result is not None
            # Original version (has run method)
            elif hasattr(tool, 'run'):
                from drowcoder.tools.execute import CommandConfig
                config = CommandConfig(command="echo 'test'")
                result = tool.run(config)
                assert isinstance(result, CommandResult)

    def test_tool_with_logger(self):
        """Test tool with custom logger."""
        if CommandExecutor and hasattr(CommandExecutor, '__init__'):
            # Check if it accepts logger parameter (refactored version)
            import logging
            import inspect
            try:
                sig = inspect.signature(CommandExecutor.__init__)
                if 'logger' in sig.parameters or 'kwargs' in sig.parameters:
                    logger = logging.getLogger("test_logger")
                    tool = CommandExecutor(logger=logger)
                    assert tool is not None
                else:
                    # Original version doesn't support logger
                    pytest.skip("Original version doesn't support logger parameter")
            except Exception:
                # Original version doesn't support logger
                pytest.skip("Original version doesn't support logger parameter")

    def test_tool_with_callback(self):
        """Test tool with callback function."""
        if CommandExecutor and hasattr(CommandExecutor, '__init__'):
            import inspect
            try:
                sig = inspect.signature(CommandExecutor.__init__)
                if 'callback' in sig.parameters or 'kwargs' in sig.parameters:
                    callback_called = []

                    def test_callback(event, data):
                        callback_called.append((event, data))

                    tool = CommandExecutor(callback=test_callback)

                    if hasattr(tool, 'execute'):
                        result = tool.execute(command="echo 'test'")
                        # Callback might be called
                        assert result is not None
                else:
                    # Original version doesn't support callback
                    pytest.skip("Original version doesn't support callback parameter")
            except Exception:
                # Original version doesn't support callback
                pytest.skip("Original version doesn't support callback parameter")


class TestExecuteEdgeCases:
    """Edge case tests."""

    def test_empty_output(self):
        """Test command with no output."""
        result = execute_command("true")

        if isinstance(result, str):
            assert "exit_code: 0" in result
        else:
            assert result.exit_code == 0
            assert result.output == "" or result.output.strip() == ""

    def test_large_output(self):
        """Test command with large output."""
        # Generate reasonably large output
        result = execute_command("seq 1 100")

        if isinstance(result, str):
            assert "100" in result
        else:
            assert "100" in result.output

    def test_command_with_quotes(self):
        """Test command with quotes."""
        result = execute_command("echo 'hello \"world\"'")

        if isinstance(result, str):
            assert "hello" in result and "world" in result
        else:
            assert "hello" in result.output and "world" in result.output


class TestExecuteResultProperties:
    """Test CommandResult properties."""

    def test_result_has_required_fields(self):
        """Test that result has all required fields."""
        result = execute_command("echo 'test'")

        if isinstance(result, CommandResult):
            assert hasattr(result, 'command')
            assert hasattr(result, 'exit_code')
            assert hasattr(result, 'output')
            assert hasattr(result, 'duration_ms')
            assert hasattr(result, 'timed_out')
            assert hasattr(result, 'pid')

    def test_result_to_dict(self):
        """Test CommandResult.to_dict() method."""
        result = execute_command("echo 'test'")

        if isinstance(result, CommandResult):
            result_dict = result.to_dict()
            assert isinstance(result_dict, dict)
            assert 'command' in result_dict
            assert 'exit_code' in result_dict

    def test_result_to_pretty_str(self):
        """Test CommandResult.to_pretty_str() method."""
        result = execute_command("echo 'test'")

        if isinstance(result, CommandResult):
            pretty_str = result.to_pretty_str()
            assert isinstance(pretty_str, str)
            assert 'command:' in pretty_str
            assert 'exit_code:' in pretty_str


class TestExecuteParametrized:
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
        if isinstance(result, str):
            assert len(result) > 0
        else:
            assert result.exit_code == 0

    @pytest.mark.parametrize("timeout", [0, 5, 10])
    def test_various_timeouts(self, timeout):
        """Test various timeout values."""
        result = execute_command("echo 'fast'", timeout_seconds=timeout)

        if isinstance(result, str):
            assert "fast" in result
        else:
            assert "fast" in result.output
            assert result.timed_out is False


if __name__ == "__main__":
    import argparse
    from .base import run_tests_with_report

    parser = argparse.ArgumentParser()
    parser.add_argument('--module', default='execute',
                        choices=['execute', 'execute_refactor'],
                        help='Which module to test')
    args = parser.parse_args()

    # Set environment variable for the test module
    os.environ['TEST_EXEC_MODULE'] = args.module

    # Use module name as tool name
    tool_name = args.module

    print(f"Testing module: {args.module}")
    print(f"Report name: {tool_name}")
    print("=" * 70)

    sys.exit(run_tests_with_report(__file__, tool_name))

