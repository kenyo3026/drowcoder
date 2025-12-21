"""
Unit tests for load tool.

Tests cover:
- Basic file loading
- Edge cases (empty, large files, special characters)
- Path handling (absolute, relative, home directory)
- Unicode and encoding
- Error conditions
- Tool class interface

Usage:
    # Run tests
    pytest src/drowcoder/tools/tools/tests/test_load.py -v

    # Or with direct execution
    python -m src.drowcoder.tools.tools.tests.test_load
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

# Import from current unified tool structure
from drowcoder.tools.tools.load import LoadTool, LoadToolResponse

# Helper function to maintain test compatibility
def load(file_path: str, ensure_abs: bool = True) -> str:
    """Wrapper function for testing - creates tool instance and calls execute"""
    tool = LoadTool()
    from drowcoder.tools.tools.base import ToolResponseType
    result = tool.execute(file_path=file_path, ensure_abs=ensure_abs, as_type=ToolResponseType.INTACT)
    return result.content


class TestLoadBasic:
    """Basic file loading tests."""

    def test_simple_file(self, tmp_path):
        """Test loading a simple text file."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        result = load(str(test_file))
        assert result == test_content

    def test_empty_file(self, tmp_path):
        """Test loading an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        result = load(str(test_file))
        assert result == ""

    def test_multiline_file(self, tmp_path):
        """Test loading a file with multiple lines."""
        test_content = "Line 1\nLine 2\nLine 3"
        test_file = tmp_path / "multiline.txt"
        test_file.write_text(test_content)

        result = load(str(test_file))
        assert result == test_content


class TestLoadEdgeCases:
    """Edge case tests for load tool."""

    def test_large_file(self, tmp_path):
        """Test loading a large file (1MB)."""
        test_content = "A" * (1024 * 1024)  # 1MB of 'A's
        test_file = tmp_path / "large.txt"
        test_file.write_text(test_content)

        result = load(str(test_file))
        assert len(result) == 1024 * 1024
        assert result == test_content

    def test_very_long_lines(self, tmp_path):
        """Test loading a file with very long lines."""
        test_content = "x" * 100000  # 100k character line
        test_file = tmp_path / "longlines.txt"
        test_file.write_text(test_content)

        result = load(str(test_file))
        assert result == test_content

    def test_many_lines(self, tmp_path):
        """Test loading a file with many lines."""
        test_content = "\n".join([f"Line {i}" for i in range(10000)])
        test_file = tmp_path / "manylines.txt"
        test_file.write_text(test_content)

        result = load(str(test_file))
        assert result.count("\n") == 9999  # 10000 lines = 9999 newlines

    def test_special_characters(self, tmp_path):
        """Test loading a file with special characters."""
        test_content = "Special: !@#$%^&*()[]{}|\\<>?/~`"
        test_file = tmp_path / "special.txt"
        test_file.write_text(test_content)

        result = load(str(test_file))
        assert result == test_content

    def test_mixed_whitespace(self, tmp_path):
        """Test loading a file with various whitespace."""
        test_content = "Tab\there\nNewline\nSecond\fForm\vVertical"
        test_file = tmp_path / "whitespace.txt"
        test_file.write_text(test_content)

        result = load(str(test_file))
        assert result == test_content


class TestLoadUnicode:
    """Unicode and encoding tests."""

    def test_unicode_content(self, tmp_path):
        """Test loading a file with Unicode characters."""
        test_content = "Unicode: café, naïve, 日本語"
        test_file = tmp_path / "unicode.txt"
        test_file.write_text(test_content, encoding='utf-8')

        result = load(str(test_file))
        assert result == test_content

    def test_chinese_text(self, tmp_path):
        """Test loading Chinese text."""
        test_content = "中文测试：你好世界"
        test_file = tmp_path / "chinese.txt"
        test_file.write_text(test_content, encoding='utf-8')

        result = load(str(test_file))
        assert result == test_content

    def test_emoji(self, tmp_path):
        """Test loading emoji characters."""
        test_content = "Emoji: 😀 🎉 🚀 ❤️"
        test_file = tmp_path / "emoji.txt"
        test_file.write_text(test_content, encoding='utf-8')

        result = load(str(test_file))
        assert result == test_content

    def test_mixed_languages(self, tmp_path):
        """Test loading mixed language content."""
        test_content = "English, 中文, 日本語, العربية, Русский"
        test_file = tmp_path / "mixed.txt"
        test_file.write_text(test_content, encoding='utf-8')

        result = load(str(test_file))
        assert result == test_content


class TestLoadPaths:
    """Path handling tests."""

    def test_absolute_path(self, tmp_path):
        """Test loading with absolute path."""
        test_file = tmp_path / "absolute.txt"
        test_content = "Absolute path test"
        test_file.write_text(test_content)

        result = load(str(test_file.absolute()))
        assert result == test_content

    def test_relative_path(self):
        """Test loading with relative path."""
        test_file = "test_relative_file.txt"
        test_content = "Relative path test"

        try:
            with open(test_file, 'w') as f:
                f.write(test_content)

            result = load(test_file)
            assert result == test_content
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_ensure_abs_true(self, tmp_path):
        """Test ensure_abs=True parameter."""
        test_file = tmp_path / "test.txt"
        test_content = "Test content"
        test_file.write_text(test_content)

        result = load(str(test_file), ensure_abs=True)
        assert result == test_content

    def test_ensure_abs_false(self, tmp_path):
        """Test ensure_abs=False parameter."""
        test_file = tmp_path / "test.txt"
        test_content = "Test content"
        test_file.write_text(test_content)

        result = load(str(test_file), ensure_abs=False)
        assert result == test_content


class TestLoadErrors:
    """Error handling tests."""

    def test_nonexistent_file(self):
        """Test loading a non-existent file."""
        test_file = "/tmp/this_file_definitely_does_not_exist_12345.txt"

        tool = LoadTool()
        from drowcoder.tools.tools.base import ToolResponseType
        result = tool.execute(test_file, as_type=ToolResponseType.INTACT)
        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error.lower()

    def test_directory_instead_of_file(self, tmp_path):
        """Test loading a directory instead of a file."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        tool = LoadTool()
        from drowcoder.tools.tools.base import ToolResponseType
        result = tool.execute(str(test_dir), as_type=ToolResponseType.INTACT)
        assert result.success is False
        assert result.error is not None

    def test_invalid_path_characters(self):
        """Test with invalid path characters."""
        test_file = "/tmp/\x00invalid\x00path.txt"

        tool = LoadTool()
        from drowcoder.tools.tools.base import ToolResponseType
        result = tool.execute(test_file, as_type=ToolResponseType.INTACT)
        assert result.success is False
        assert result.error is not None


class TestLoadToolClass:
    """Tests for LoadTool class interface."""

    def test_tool_execute_returns_result(self, tmp_path):
        """Test that tool.execute() returns LoadToolResponse."""
        tool = LoadTool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        from drowcoder.tools.tools.base import ToolResponseType
        result = tool.execute(str(test_file), as_type=ToolResponseType.INTACT)
        assert isinstance(result, LoadToolResponse)
        assert result.success is True
        assert result.content == "Test content"

    def test_tool_with_logger(self, tmp_path):
        """Test tool with custom logger."""
        import logging
        logger = logging.getLogger("test_logger")
        tool = LoadTool(logger=logger)
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        from drowcoder.tools.tools.base import ToolResponseType
        result = tool.execute(str(test_file), as_type=ToolResponseType.INTACT)
        assert result.success is True

    def test_tool_with_callback(self, tmp_path):
        """Test tool with callback function."""
        callback_called = []

        def test_callback(event, data=None):
            callback_called.append(event)

        tool = LoadTool(callback=test_callback)
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        from drowcoder.tools.tools.base import ToolResponseType
        result = tool.execute(str(test_file), as_type=ToolResponseType.INTACT)
        assert result.success is True

    def test_tool_metadata(self, tmp_path):
        """Test tool result metadata."""
        tool = LoadTool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        from drowcoder.tools.tools.base import ToolResponseType
        result = tool.execute(str(test_file), as_type=ToolResponseType.INTACT)
        assert result.metadata is not None
        from drowcoder.tools.tools.load import LoadToolResponseMetadata
        assert isinstance(result.metadata, LoadToolResponseMetadata)
        assert result.metadata.file_path is not None
        assert result.metadata.file_size == 12

if __name__ == "__main__":
    import argparse
    from .base import run_tests_with_report

    parser = argparse.ArgumentParser()
    parser.add_argument('--module', default='load', choices=['load', 'load_refactor'],
                        help='Which load module to test: load or load_refactor')
    args = parser.parse_args()

    # Set environment variable for the test module
    os.environ['TEST_LOAD_MODULE'] = args.module

    # Use module name as tool name if not specified
    tool_name = args.module

    print(f"Testing module: {args.module}")
    print(f"Report name: {tool_name}")
    print("=" * 70)

    sys.exit(run_tests_with_report(__file__, tool_name))

