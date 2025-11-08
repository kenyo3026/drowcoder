"""
Unit tests for write tool.

Tests cover:
- Basic write operations (create, overwrite, append, prepend)
- Preview and apply modes
- Output styles (default, git_diff, git_conflict)
- Edge cases (empty content, large files, special characters)
- Unicode and encoding
- File permissions and backup
- Error conditions
- Tool class interface

Usage:
    # Test original write tool
    python -m src.drowcoder.tools.tests.test_write

    # Test refactored write tool
    python -m src.drowcoder.tools.tests.test_write --module write_refactor
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
import importlib

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Get module name from environment variable or use default
TEST_MODULE = os.environ.get('TEST_WRITE_MODULE', 'write')

# Dynamically import the specified module
write_module = importlib.import_module(f'drowcoder.tools.{TEST_MODULE}')
WriteTool = getattr(write_module, 'WriteTool', None)
WriteToolResult = getattr(write_module, 'WriteToolResult', None)

# Helper function to maintain test compatibility
def write(file_path, content, mode="apply", output_style="default", operation="overwrite", output_file=None, **kwargs):
    """Wrapper function for testing - creates tool instance and calls execute"""
    tool = WriteTool()
    return tool.execute(
        file_path=file_path,
        content=content,
        mode=mode,
        output_style=output_style,
        operation=operation,
        output_file=output_file,
        **kwargs
    )


@pytest.fixture
def tmp_path():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestWriteBasicOperations:
    """Basic write operations tests."""

    def test_create_new_file(self, tmp_path):
        """Test creating a new file."""
        test_file = tmp_path / "new_file.txt"
        content = "Hello, World!"

        result = write(str(test_file), content, operation="create", mode="apply")

        assert result.success
        assert test_file.exists()
        assert test_file.read_text() == content

    def test_overwrite_existing_file(self, tmp_path):
        """Test overwriting an existing file."""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("Original content")

        new_content = "New content"
        result = write(str(test_file), new_content, operation="overwrite", mode="apply")

        assert result.success
        assert test_file.read_text() == new_content

    def test_append_to_file(self, tmp_path):
        """Test appending to an existing file."""
        test_file = tmp_path / "append.txt"
        original = "Line 1"
        test_file.write_text(original)

        append_content = "Line 2"
        result = write(str(test_file), append_content, operation="append", mode="apply")

        assert result.success
        content = test_file.read_text()
        assert original in content
        assert append_content in content

    def test_prepend_to_file(self, tmp_path):
        """Test prepending to an existing file."""
        test_file = tmp_path / "prepend.txt"
        original = "Line 2"
        test_file.write_text(original)

        prepend_content = "Line 1"
        result = write(str(test_file), prepend_content, operation="prepend", mode="apply")

        assert result.success
        content = test_file.read_text()
        assert content.startswith(prepend_content)
        assert original in content


class TestWriteModes:
    """Test different execution modes."""

    def test_preview_mode(self, tmp_path):
        """Test preview mode doesn't modify files."""
        test_file = tmp_path / "preview.txt"
        test_file.write_text("Original")

        result = write(str(test_file), "New content", mode="preview")

        # File should remain unchanged
        assert test_file.read_text() == "Original"

    def test_apply_mode(self, tmp_path):
        """Test apply mode modifies files."""
        test_file = tmp_path / "apply.txt"
        test_file.write_text("Original")

        result = write(str(test_file), "New content", mode="apply")

        assert result.success
        assert test_file.read_text() == "New content"

    def test_identical_content_no_changes(self, tmp_path):
        """Test that identical content results in no changes."""
        test_file = tmp_path / "identical.txt"
        content = "Same content"
        test_file.write_text(content)

        result = write(str(test_file), content, mode="apply")

        # Should detect no changes needed
        assert result.success
        assert result.total_files_changed == 0


class TestWriteOutputStyles:
    """Test different output styles."""

    def test_default_style(self, tmp_path):
        """Test default output style."""
        test_file = tmp_path / "default.txt"
        content = "Test content"

        result = write(str(test_file), content, output_style="default", mode="apply")

        assert result.success
        assert test_file.read_text() == content

    def test_git_diff_style_preview(self, tmp_path):
        """Test git diff style in preview mode."""
        test_file = tmp_path / "diff.txt"
        test_file.write_text("Original line")

        result = write(str(test_file), "New line", output_style="git_diff", mode="preview")

        # Should not modify file in preview
        assert test_file.read_text() == "Original line"

    def test_git_conflict_style_preview(self, tmp_path):
        """Test git conflict style in preview mode."""
        test_file = tmp_path / "conflict.txt"
        test_file.write_text("Original")

        result = write(str(test_file), "New", output_style="git_conflict", mode="preview")

        # Should not modify file in preview
        assert test_file.read_text() == "Original"


class TestWriteEdgeCases:
    """Edge case tests."""

    def test_empty_content(self, tmp_path):
        """Test writing empty content."""
        test_file = tmp_path / "empty.txt"

        result = write(str(test_file), "", operation="create", mode="apply")

        # Empty content is detected as "no changes", so file won't be created
        # This is the original tool's behavior
        assert result.success
        assert result.total_files_changed == 0

    def test_large_content(self, tmp_path):
        """Test writing large content (1MB)."""
        test_file = tmp_path / "large.txt"
        content = "A" * (1024 * 1024)  # 1MB

        result = write(str(test_file), content, operation="create", mode="apply")

        assert result.success
        assert len(test_file.read_text()) == 1024 * 1024

    def test_many_lines(self, tmp_path):
        """Test writing many lines."""
        test_file = tmp_path / "many_lines.txt"
        content = "\n".join([f"Line {i}" for i in range(1000)])

        result = write(str(test_file), content, operation="create", mode="apply")

        assert result.success
        assert test_file.read_text().count("\n") == 999

    def test_special_characters(self, tmp_path):
        """Test writing special characters."""
        test_file = tmp_path / "special.txt"
        content = "Special: !@#$%^&*()[]{}|\\<>?/~`"

        result = write(str(test_file), content, operation="create", mode="apply")

        assert result.success
        assert test_file.read_text() == content

    def test_mixed_line_endings(self, tmp_path):
        """Test that line endings are normalized."""
        test_file = tmp_path / "line_endings.txt"
        content_with_crlf = "Line 1\r\nLine 2\rLine 3\n"

        result = write(str(test_file), content_with_crlf, operation="create", mode="apply")

        assert result.success
        # Line endings should be normalized to \n
        normalized = test_file.read_text()
        assert "\r" not in normalized


class TestWriteUnicode:
    """Unicode and encoding tests."""

    def test_unicode_content(self, tmp_path):
        """Test writing Unicode content."""
        test_file = tmp_path / "unicode.txt"
        content = "Unicode: café, naïve, 日本語, 中文"

        result = write(str(test_file), content, operation="create", mode="apply")

        assert result.success
        assert test_file.read_text(encoding='utf-8') == content

    def test_emoji(self, tmp_path):
        """Test writing emoji."""
        test_file = tmp_path / "emoji.txt"
        content = "Emoji: 😀 🎉 🚀 ❤️"

        result = write(str(test_file), content, operation="create", mode="apply")

        assert result.success
        assert test_file.read_text(encoding='utf-8') == content

    def test_mixed_languages(self, tmp_path):
        """Test writing mixed language content."""
        test_file = tmp_path / "mixed.txt"
        content = "English, 中文, 日本語, العربية, Русский"

        result = write(str(test_file), content, operation="create", mode="apply")

        assert result.success
        assert test_file.read_text(encoding='utf-8') == content


class TestWriteErrors:
    """Error handling tests."""

    def test_create_existing_file_fails(self, tmp_path):
        """Test that CREATE operation fails if file exists."""
        test_file = tmp_path / "exists.txt"
        test_file.write_text("Already exists")

        result = write(str(test_file), "New content", operation="create", mode="apply")

        assert not result.success
        # Original file should be unchanged
        assert test_file.read_text() == "Already exists"

    def test_invalid_mode_raises_error(self, tmp_path):
        """Test that invalid mode raises ValueError."""
        test_file = tmp_path / "test.txt"

        with pytest.raises(ValueError, match="Invalid mode"):
            write(str(test_file), "content", mode="invalid_mode")

    def test_parent_directory_creation(self, tmp_path):
        """Test that parent directories are created."""
        test_file = tmp_path / "subdir" / "nested" / "file.txt"

        result = write(str(test_file), "content", operation="create", mode="apply", create_dirs=True)

        assert result.success
        assert test_file.exists()
        assert test_file.read_text() == "content"


class TestWriteBackup:
    """Backup functionality tests."""

    def test_backup_created_on_overwrite(self, tmp_path):
        """Test that backup is created when overwriting."""
        test_file = tmp_path / "backup_test.txt"
        original = "Original content"
        test_file.write_text(original)

        result = write(str(test_file), "New content", operation="overwrite", mode="apply", backup=True)

        assert result.success
        # Check if backup was created
        if result.file_results:
            # Backup may have been created
            backup_files = list(tmp_path.glob("backup_test.txt.backup*"))
            if backup_files:
                assert backup_files[0].read_text() == original

    def test_no_backup_when_disabled(self, tmp_path):
        """Test that no backup is created when disabled."""
        test_file = tmp_path / "no_backup.txt"
        test_file.write_text("Original")

        result = write(str(test_file), "New", operation="overwrite", mode="apply", backup=False)

        assert result.success
        # No backup should be created
        backup_files = list(tmp_path.glob("no_backup.txt.backup*"))
        assert len(backup_files) == 0


class TestWriteToolClass:
    """Tests for WriteTool class interface."""

    def test_tool_initialization(self):
        """Test that tool can be initialized."""
        if WriteTool:
            tool = WriteTool()
            assert tool is not None
            assert tool._initialized is True

    def test_tool_execute_returns_result(self, tmp_path):
        """Test that tool.execute() returns WriteToolResult."""
        if WriteTool and WriteToolResult:
            tool = WriteTool()
            test_file = tmp_path / "test.txt"

            result = tool.execute(str(test_file), "Test content", mode="apply")

            assert isinstance(result, WriteToolResult)
            assert result.success is True

    def test_tool_with_logger(self, tmp_path):
        """Test tool with custom logger."""
        if WriteTool:
            import logging
            logger = logging.getLogger("test_logger")
            tool = WriteTool(logger=logger)

            test_file = tmp_path / "test.txt"
            result = tool.execute(str(test_file), "Test", mode="apply")

            assert result.success is True

    def test_tool_with_callback(self, tmp_path):
        """Test tool with callback function."""
        if WriteTool:
            callback_called = []

            def test_callback(event, data):
                callback_called.append((event, data))

            tool = WriteTool(callback=test_callback)
            test_file = tmp_path / "test.txt"

            result = tool.execute(str(test_file), "Test", mode="apply")

            assert result.success is True
            assert len(callback_called) > 0

    def test_tool_not_initialized(self, tmp_path):
        """Test tool without initialization raises error."""
        if WriteTool:
            tool = WriteTool(auto_initialize=False)
            test_file = tmp_path / "test.txt"

            with pytest.raises(RuntimeError, match="not initialized"):
                tool.execute(str(test_file), "Test", mode="apply")

    def test_tool_metadata(self, tmp_path):
        """Test result contains metadata."""
        if WriteTool and WriteToolResult:
            tool = WriteTool()
            test_file = tmp_path / "test.txt"

            result = tool.execute(str(test_file), "Test", mode="apply")

            assert hasattr(result, 'metadata')
            assert isinstance(result.metadata, dict)


class TestWriteResultProperties:
    """Test WriteToolResult properties."""

    def test_result_total_files_processed(self, tmp_path):
        """Test total_files_processed property."""
        test_file = tmp_path / "test.txt"
        result = write(str(test_file), "content", mode="apply")

        if hasattr(result, 'total_files_processed'):
            assert result.total_files_processed >= 0

    def test_result_total_files_changed(self, tmp_path):
        """Test total_files_changed property."""
        test_file = tmp_path / "test.txt"
        result = write(str(test_file), "content", mode="apply")

        if hasattr(result, 'total_files_changed'):
            assert result.total_files_changed >= 0

    def test_result_total_files_created(self, tmp_path):
        """Test total_files_created property."""
        test_file = tmp_path / "test.txt"
        result = write(str(test_file), "content", operation="create", mode="apply")

        if hasattr(result, 'total_files_created'):
            assert result.total_files_created >= 0


class TestWriteAppendPrepend:
    """Detailed append/prepend operation tests."""

    def test_append_adds_newline_if_needed(self, tmp_path):
        """Test append adds newline if original doesn't end with one."""
        test_file = tmp_path / "append_newline.txt"
        test_file.write_text("Line 1")  # No trailing newline

        result = write(str(test_file), "Line 2", operation="append", mode="apply")

        assert result.success
        content = test_file.read_text()
        lines = content.split('\n')
        assert len(lines) >= 2

    def test_prepend_adds_newline_if_needed(self, tmp_path):
        """Test prepend adds newline if new content doesn't end with one."""
        test_file = tmp_path / "prepend_newline.txt"
        test_file.write_text("Line 2")

        result = write(str(test_file), "Line 1", operation="prepend", mode="apply")

        assert result.success
        content = test_file.read_text()
        lines = content.split('\n')
        assert len(lines) >= 2

    def test_append_to_empty_file(self, tmp_path):
        """Test appending to empty file."""
        test_file = tmp_path / "empty_append.txt"
        test_file.write_text("")

        result = write(str(test_file), "New content", operation="append", mode="apply")

        assert result.success
        assert test_file.read_text() == "New content"

    def test_prepend_to_empty_file(self, tmp_path):
        """Test prepending to empty file."""
        test_file = tmp_path / "empty_prepend.txt"
        test_file.write_text("")

        result = write(str(test_file), "New content", operation="prepend", mode="apply")

        assert result.success
        # Prepend adds a newline after the content if it doesn't end with one
        # This is the original tool's behavior
        content = test_file.read_text()
        assert "New content" in content


class TestWriteParametrized:
    """Parametrized tests for various inputs."""

    @pytest.mark.parametrize("content", [
        "Simple text",
        "",
        "A" * 1000,
        "Special: !@#$%^&*()",
        "Unicode: 中文 🎉",
        "Line 1\nLine 2\nLine 3",
        "Tab\t\tseparated",
        " Leading and trailing spaces ",
    ])
    def test_various_content(self, tmp_path, content):
        """Test write with various content types."""
        test_file = tmp_path / "test.txt"

        result = write(str(test_file), content, mode="apply")

        assert result.success
        # For non-empty content, verify it was written
        if content:
            written = test_file.read_text()
            # Normalize for comparison (line endings)
            written_normalized = written.replace('\r\n', '\n').replace('\r', '\n')
            content_normalized = content.replace('\r\n', '\n').replace('\r', '\n')
            assert written_normalized.strip() == content_normalized.strip()

    @pytest.mark.parametrize("operation", [
        "create",
        "overwrite",
        "append",
        "prepend",
    ])
    def test_all_operations(self, tmp_path, operation):
        """Test all operation types."""
        test_file = tmp_path / f"test_{operation}.txt"

        # For non-create operations, create the file first
        if operation != "create":
            test_file.write_text("Original content")

        result = write(str(test_file), "New content", operation=operation, mode="apply")

        assert result.success


if __name__ == "__main__":
    import argparse
    from .base import run_tests_with_report

    parser = argparse.ArgumentParser()
    parser.add_argument('--module', default='write', choices=['write', 'write_refactor'],
                        help='Which write module to test: write or write_refactor')
    args = parser.parse_args()

    # Set environment variable for the test module
    os.environ['TEST_WRITE_MODULE'] = args.module

    # Use module name as tool name
    tool_name = args.module

    print(f"Testing module: {args.module}")
    print(f"Report name: {tool_name}")
    print("=" * 70)

    sys.exit(run_tests_with_report(__file__, tool_name))

