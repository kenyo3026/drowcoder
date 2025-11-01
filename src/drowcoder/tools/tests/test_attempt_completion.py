"""
Unit tests for attempt_completion tool.

Tests cover:
- Basic functionality
- Edge cases (empty, very long, special characters)
- Unicode and emoji support
- Newlines and whitespace
- Error conditions
- Tool class interface

Usage:
    # Test original attempt_completion tool
    python -m src.drowcoder.tools.tests.test_attempt_completion

    # Test refactored attempt_completion tool
    python -m src.drowcoder.tools.tests.test_attempt_completion --module attempt_completion_refactor
"""

import pytest
import sys
import os
from pathlib import Path
import importlib

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Get module name from environment variable or use default
TEST_MODULE = os.environ.get('TEST_ATTEMPT_COMPLETION_MODULE', 'attempt_completion')

# Dynamically import the specified module
ac_module = importlib.import_module(f'drowcoder.tools.{TEST_MODULE}')
attempt_completion = ac_module.attempt_completion
AttemptCompletionTool = ac_module.AttemptCompletionTool
AttemptCompletionResult = ac_module.AttemptCompletionResult


class TestAttemptCompletionBasic:
    """Basic functionality tests."""

    def test_simple_string(self):
        """Test with simple string."""
        result = "Implemented new feature"
        expected = f"Task completed successfully: {result}"

        assert attempt_completion(result) == expected

    def test_empty_string(self):
        """Test with empty string."""
        result = ""
        expected = "Task completed successfully: "

        assert attempt_completion(result) == expected

    def test_single_char(self):
        """Test with single character."""
        result = "X"
        expected = "Task completed successfully: X"

        assert attempt_completion(result) == expected

    def test_whitespace_only(self):
        """Test with whitespace only."""
        result = "   "
        expected = "Task completed successfully:    "

        assert attempt_completion(result) == expected


class TestAttemptCompletionEdgeCases:
    """Edge case tests."""

    def test_very_long_string(self):
        """Test with very long string (10000 chars)."""
        result = "A" * 10000
        expected = f"Task completed successfully: {'A' * 10000}"

        assert attempt_completion(result) == expected

    def test_special_characters(self):
        """Test with special characters."""
        result = "Fixed: @#$%^&*()_+-=[]{}|;':\",./<>?"
        expected = f"Task completed successfully: {result}"

        assert attempt_completion(result) == expected

    def test_newlines(self):
        """Test with newlines."""
        result = "Task 1\nTask 2\nTask 3"
        expected = f"Task completed successfully: {result}"

        assert attempt_completion(result) == expected

    def test_tabs(self):
        """Test with tabs."""
        result = "Item\t\tValue\t\tStatus"
        expected = f"Task completed successfully: {result}"

        assert attempt_completion(result) == expected

    def test_mixed_whitespace(self):
        """Test with mixed whitespace."""
        result = " \t\n\r  Mixed  \t\n  whitespace  \r\n "
        expected = f"Task completed successfully: {result}"

        assert attempt_completion(result) == expected


class TestAttemptCompletionUnicode:
    """Unicode and internationalization tests."""

    def test_chinese_characters(self):
        """Test with Chinese characters."""
        result = "完成了功能实现"
        expected = f"Task completed successfully: {result}"

        assert attempt_completion(result) == expected

    def test_emoji(self):
        """Test with emoji."""
        result = "Feature complete 🎉 🚀 ✨"
        expected = f"Task completed successfully: {result}"

        assert attempt_completion(result) == expected

    def test_mixed_unicode(self):
        """Test with mixed unicode."""
        result = "Completed 完成 done ✓ успешно 成功"
        expected = f"Task completed successfully: {result}"

        assert attempt_completion(result) == expected

    def test_rtl_text(self):
        """Test with RTL (Right-to-Left) text."""
        result = "مكتمل successfully completed"
        expected = f"Task completed successfully: {result}"

        assert attempt_completion(result) == expected


class TestAttemptCompletionFormatting:
    """Formatting and structure tests."""

    def test_bullet_list(self):
        """Test with bullet list."""
        result = """Completed:
- Feature A
- Feature B
- Feature C"""
        expected = f"Task completed successfully: {result}"

        assert attempt_completion(result) == expected

    def test_numbered_list(self):
        """Test with numbered list."""
        result = """1. First task
2. Second task
3. Third task"""
        expected = f"Task completed successfully: {result}"

        assert attempt_completion(result) == expected

    def test_markdown_like(self):
        """Test with markdown-like formatting."""
        result = """# Completed Tasks
## Major
- Task 1
## Minor
- Task 2"""
        expected = f"Task completed successfully: {result}"

        assert attempt_completion(result) == expected

    def test_code_snippet(self):
        """Test with code snippet."""
        result = 'Fixed bug in function: def test():\n    return True'
        expected = f"Task completed successfully: {result}"

        assert attempt_completion(result) == expected


class TestAttemptCompletionClass:
    """Test the class-based interface."""

    def test_tool_initialization(self):
        """Test tool can be initialized."""
        tool = AttemptCompletionTool()
        assert tool is not None
        assert tool._initialized is True

    def test_tool_execute_returns_result(self):
        """Test tool execute returns AttemptCompletionResult."""
        tool = AttemptCompletionTool()
        result = tool.execute(result="Test")

        assert isinstance(result, AttemptCompletionResult)
        assert result.success is True
        assert "Task completed successfully: Test" in result.result

    def test_tool_with_logger(self):
        """Test tool with custom logger."""
        import logging
        logger = logging.getLogger("test")

        tool = AttemptCompletionTool(logger=logger)
        result = tool.execute(result="Test")

        assert result.success is True

    def test_tool_with_callback(self):
        """Test tool with callback."""
        callback_data = []

        def callback(event, data):
            callback_data.append((event, data))

        tool = AttemptCompletionTool(callback=callback)
        result = tool.execute(result="Test")

        assert result.success is True
        assert len(callback_data) == 1
        assert callback_data[0][0] == "task_completed"

    def test_tool_not_initialized(self):
        """Test tool without initialization raises error."""
        tool = AttemptCompletionTool(auto_initialize=False)

        with pytest.raises(RuntimeError, match="not initialized"):
            tool.execute(result="Test")

    def test_tool_metadata(self):
        """Test result contains metadata."""
        tool = AttemptCompletionTool()
        result = tool.execute(result="Test")

        assert "metadata" in result.__dict__
        assert result.metadata["tool"] == "attempt_completion"
        assert result.metadata["result_length"] == 4


class TestAttemptCompletionParametrized:
    """Parametrized tests for various inputs."""

    @pytest.mark.parametrize("test_input", [
        "Simple test",
        "",
        "A" * 1000,
        "Special: !@#$%^&*()",
        "Unicode: 中文 🎉",
        "Line 1\nLine 2\nLine 3",
        "Tab\t\tseparated",
        " Leading and trailing spaces ",
    ])
    def test_various_inputs(self, test_input):
        """Test attempt_completion with various inputs."""
        result = attempt_completion(test_input)
        expected = f"Task completed successfully: {test_input}"

        assert result == expected

if __name__ == "__main__":
    import argparse
    from .base import run_tests_with_report

    parser = argparse.ArgumentParser()
    parser.add_argument('--module', default='attempt_completion',
                        choices=['attempt_completion', 'attempt_completion_refactor'],
                        help='Which attempt_completion module to test')
    args = parser.parse_args()

    # Set environment variable for the test module
    os.environ['TEST_ATTEMPT_COMPLETION_MODULE'] = args.module

    # Use module name as tool name if not specified
    tool_name = args.module

    print(f"Testing module: {args.module}")
    print(f"Report name: {tool_name}")
    print("=" * 70)

    sys.exit(run_tests_with_report(__file__, tool_name))


