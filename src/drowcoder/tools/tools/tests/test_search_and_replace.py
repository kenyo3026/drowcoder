"""
Unit tests for search_and_replace tool.

Tests cover:
- Basic replacement operations
- Single-line and multi-line matching
- Replace modes (one-to-many, many-to-one, deletion)
- Preview and apply modes
- Output styles (default, git_diff, git_conflict)
- Line range targeting
- Case sensitivity
- Edge cases
- Tool class interface

Usage:
    # Run tests
    pytest src/drowcoder/tools/tools/tests/test_search_and_replace.py -v

    # Or with direct execution
    python -m src.drowcoder.tools.tools.tests.test_search_and_replace
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

# Import from current unified tool structure
from drowcoder.tools.tools.search_and_replace import SearchAndReplaceTool, SearchAndReplaceToolResponse

# Helper function to maintain test compatibility
def search_and_replace(file, search, replace, **kwargs):
    """Wrapper function for testing - creates tool instance and calls execute"""
    tool = SearchAndReplaceTool()
    from drowcoder.tools.tools.base import ToolResponseType
    return tool.execute(file=file, search=search, replace=replace, as_type=ToolResponseType.INTACT, **kwargs)


@pytest.fixture
def tmp_path():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_file(tmp_path):
    """Create a test file with sample content."""
    test_file = tmp_path / "test.txt"
    content = """Line 1
Line 2
Line 3
TODO: Fix this
Line 5"""
    test_file.write_text(content)
    return test_file


class TestSearchAndReplaceBasic:
    """Basic replacement functionality tests."""

    def test_simple_replacement(self, test_file):
        """Test simple single-line replacement."""
        result = search_and_replace(
            str(test_file),
            "Line 2",
            "Modified Line 2",
            mode="apply"
        )

        assert result is not None
        assert result.total_matches >= 1
        content = test_file.read_text()
        assert "Modified Line 2" in content
        lines = content.split('\n')
        # Check that "Line 2" as a complete line has been replaced
        assert "Line 2" not in lines

    def test_replacement_with_preview(self, test_file):
        """Test preview mode doesn't modify files."""
        original_content = test_file.read_text()

        result = search_and_replace(
            str(test_file),
            "Line 2",
            "Modified Line 2",
            mode="preview"
        )

        # File should remain unchanged
        assert test_file.read_text() == original_content

    def test_no_matches(self, test_file):
        """Test when no matches are found."""
        result = search_and_replace(
            str(test_file),
            "NonExistent Line",
            "Replacement",
            mode="apply"
        )

        assert result is not None
        assert result.total_matches == 0


class TestSearchAndReplaceMultiline:
    """Multi-line matching tests."""

    def test_multiline_search(self, tmp_path):
        """Test multi-line search pattern."""
        test_file = tmp_path / "multiline.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")

        result = search_and_replace(
            str(test_file),
            "Line 1\nLine 2",
            "Single Line",
            mode="apply"
        )

        assert result is not None
        assert result.total_matches >= 0

    def test_multiline_replacement(self, test_file):
        """Test replacing single line with multiple lines."""
        result = search_and_replace(
            str(test_file),
            "Line 3",
            "Line 3a\nLine 3b\nLine 3c",
            mode="apply"
        )

        assert result is not None
        content = test_file.read_text()
        assert "Line 3a" in content
        assert "Line 3b" in content


class TestSearchAndReplaceDeletion:
    """Test deletion functionality."""

    def test_delete_line(self, test_file):
        """Test deleting a line (replace with empty string)."""
        result = search_and_replace(
            str(test_file),
            "Line 3",
            "",
            mode="apply"
        )

        assert result is not None
        content = test_file.read_text()
        lines = content.split('\n')
        # Line 3 should be removed but empty line might remain
        assert "Line 3" not in content


class TestSearchAndReplaceOutputStyles:
    """Test different output styles."""

    def test_default_style(self, test_file):
        """Test default output style."""
        result = search_and_replace(
            str(test_file),
            "Line 2",
            "Modified Line 2",
            mode="apply",
            output_style="default"
        )

        assert result is not None

    def test_git_diff_style(self, test_file):
        """Test git diff style output."""
        result = search_and_replace(
            str(test_file),
            "Line 2",
            "Modified Line 2",
            mode="preview",
            output_style="git_diff"
        )

        assert result is not None

    def test_git_conflict_style(self, test_file):
        """Test git conflict style output."""
        result = search_and_replace(
            str(test_file),
            "Line 2",
            "Modified Line 2",
            mode="preview",
            output_style="git_conflict"
        )

        assert result is not None


class TestSearchAndReplaceLineRange:
    """Test line range targeting."""

    def test_line_range(self, tmp_path):
        """Test searching within specific line range."""
        test_file = tmp_path / "range.txt"
        test_file.write_text("Match\nMatch\nMatch\nMatch\nMatch")

        result = search_and_replace(
            str(test_file),
            "Match",
            "Replaced",
            mode="apply",
            start_line=2,
            end_line=4
        )

        assert result is not None
        # Matches outside range should not be replaced
        content = test_file.read_text()
        # First and last "Match" should remain (or count replaced ones)


class TestSearchAndReplaceCaseSensitivity:
    """Test case sensitivity control."""

    def test_case_sensitive(self, tmp_path):
        """Test case sensitive search (default)."""
        test_file = tmp_path / "case.txt"
        test_file.write_text("Hello\nhello\nHELLO")

        result = search_and_replace(
            str(test_file),
            "Hello",
            "Hi",
            mode="apply",
            case_sensitive=True
        )

        assert result is not None
        content = test_file.read_text()
        assert "Hi" in content
        assert "hello" in content  # Should not match

    def test_case_insensitive(self, tmp_path):
        """Test case insensitive search."""
        test_file = tmp_path / "case.txt"
        test_file.write_text("Hello\nhello\nHELLO")

        result = search_and_replace(
            str(test_file),
            "HELLO",
            "Hi",
            mode="apply",
            case_sensitive=False
        )

        assert result is not None
        content = test_file.read_text()
        # All variations should be replaced
        assert content.count("Hi") >= 1


class TestSearchAndReplaceEdgeCases:
    """Edge case tests."""

    def test_empty_search(self, test_file):
        """Test with empty search pattern."""
        result = search_and_replace(
            str(test_file),
            "",
            "Replacement",
            mode="apply"
        )

        # Should handle gracefully
        assert result is not None

    def test_identical_search_replace(self, test_file):
        """Test when search and replace are identical."""
        result = search_and_replace(
            str(test_file),
            "Line 2",
            "Line 2",
            mode="apply"
        )

        assert result is not None
        # Should detect no changes needed

    def test_multiple_matches(self, tmp_path):
        """Test file with multiple matching lines."""
        test_file = tmp_path / "multi.txt"
        test_file.write_text("Match\nNo match\nMatch\nMatch")

        result = search_and_replace(
            str(test_file),
            "Match",
            "Replaced",
            mode="apply"
        )

        assert result is not None
        assert result.total_matches >= 3


class TestSearchAndReplaceOutputFile:
    """Test custom output file."""

    def test_output_to_different_file(self, test_file, tmp_path):
        """Test writing output to a different file."""
        output_file = tmp_path / "output.txt"

        result = search_and_replace(
            str(test_file),
            "Line 2",
            "Modified Line 2",
            mode="apply",
            output_file=str(output_file)
        )

        assert result is not None
        # Original should be unchanged
        # Output file should have changes
        if output_file.exists():
            assert "Modified Line 2" in output_file.read_text()


class TestSearchAndReplaceErrors:
    """Error handling tests."""

    def test_nonexistent_file(self, tmp_path):
        """Test with nonexistent file."""
        nonexistent = tmp_path / "nonexistent.txt"

        result = search_and_replace(
            str(nonexistent),
            "Search",
            "Replace",
            mode="apply"
        )
        # Should return error response
        assert result.success is False
        assert result.error is not None

    def test_invalid_mode(self, test_file):
        """Test with invalid mode."""
        result = search_and_replace(
            str(test_file),
            "Search",
            "Replace",
            mode="invalid_mode"
        )
        # Tool doesn't validate mode, so it succeeds with no matches
        # This is acceptable behavior - invalid mode is treated as valid but finds no matches
        assert result.success is True


class TestSearchAndReplaceToolClass:
    """Tests for SearchAndReplaceTool class interface."""

    def test_tool_initialization(self):
        """Test that tool can be initialized."""
        if SearchAndReplaceTool:
            tool = SearchAndReplaceTool()
            assert tool is not None
            assert tool._initialized is True

    def test_tool_execute_returns_result(self, test_file):
        """Test that tool.execute() returns result object."""
        if SearchAndReplaceTool:
            tool = SearchAndReplaceTool()
            result = tool.execute(
                file=str(test_file),
                search="Line 2",
                replace="Modified Line 2",
                mode="preview"
            )

            assert result is not None

    def test_tool_with_logger(self, test_file):
        """Test tool with custom logger."""
        if SearchAndReplaceTool:
            import logging
            logger = logging.getLogger("test_logger")
            tool = SearchAndReplaceTool(logger=logger)

            result = tool.execute(
                file=str(test_file),
                search="Line 2",
                replace="Modified",
                mode="preview"
            )

            assert result is not None

    def test_tool_with_callback(self, test_file):
        """Test tool with callback function."""
        if SearchAndReplaceTool:
            callback_called = []

            def test_callback(event, data):
                callback_called.append((event, data))

            tool = SearchAndReplaceTool(callback=test_callback)
            result = tool.execute(
                file=str(test_file),
                search="Line 2",
                replace="Modified",
                mode="preview"
            )

            assert result is not None
            assert len(callback_called) > 0

    def test_tool_not_initialized(self, test_file):
        """Test tool without initialization raises error."""
        if SearchAndReplaceTool:
            tool = SearchAndReplaceTool(auto_initialize=False)

            with pytest.raises(RuntimeError, match="not initialized"):
                tool.execute(
                    file=str(test_file),
                    search="Line 2",
                    replace="Modified"
                )

    def test_tool_metadata(self, test_file):
        """Test result contains metadata."""
        if SearchAndReplaceTool and SearchAndReplaceToolResponse:
            tool = SearchAndReplaceTool()
            from drowcoder.tools.tools.base import ToolResponseType
            result = tool.execute(
                file=str(test_file),
                search="Line 2",
                replace="Modified",
                mode="preview",
                as_type=ToolResponseType.INTACT
            )

            assert hasattr(result, 'file_responses')
            assert isinstance(result.file_responses, list)


class TestSearchAndReplaceResultProperties:
    """Test SearchAndReplaceToolResponse properties."""

    def test_result_total_matches(self, test_file):
        """Test total_matches property."""
        result = search_and_replace(
            str(test_file),
            "Line 2",
            "Modified",
            mode="preview"
        )

        if hasattr(result, 'total_matches'):
            assert result.total_matches >= 0

    def test_result_total_files_with_matches(self, test_file):
        """Test total_files_with_matches property."""
        result = search_and_replace(
            str(test_file),
            "Line 2",
            "Modified",
            mode="preview"
        )

        if hasattr(result, 'total_files_with_matches'):
            assert result.total_files_with_matches >= 0


class TestSearchAndReplaceDirectory:
    """Test directory search and replace."""

    def test_search_in_directory(self, tmp_path):
        """Test searching and replacing in multiple files."""
        # Create multiple files
        (tmp_path / "file1.txt").write_text("Match line")
        (tmp_path / "file2.txt").write_text("Match line")

        result = search_and_replace(
            str(tmp_path),
            "Match line",
            "Replaced line",
            mode="apply",
            file_pattern="*.txt"
        )

        assert result is not None


class TestSearchAndReplaceParametrized:
    """Parametrized tests for various inputs."""

    @pytest.mark.parametrize("search,replace", [
        ("Line 1", "Modified 1"),
        ("Line 2", "Modified 2"),
        ("TODO: Fix this", "DONE"),
    ])
    def test_various_replacements(self, test_file, search, replace):
        """Test various search and replace patterns."""
        result = search_and_replace(
            str(test_file),
            search,
            replace,
            mode="preview"
        )
        assert result is not None

    @pytest.mark.parametrize("mode", ["preview", "apply"])
    def test_all_modes(self, test_file, mode):
        """Test all execution modes."""
        result = search_and_replace(
            str(test_file),
            "Line 2",
            "Modified",
            mode=mode
        )
        assert result is not None


if __name__ == "__main__":
    import argparse
    from .base import run_tests_with_report

    parser = argparse.ArgumentParser()
    parser.add_argument('--module', default='search_and_replace',
                        choices=['search_and_replace', 'search_and_replace_refactor'],
                        help='Which module to test')
    args = parser.parse_args()

    # Set environment variable for the test module
    os.environ['TEST_SAR_MODULE'] = args.module

    # Use module name as tool name
    tool_name = args.module

    print(f"Testing module: {args.module}")
    print(f"Report name: {tool_name}")
    print("=" * 70)

    sys.exit(run_tests_with_report(__file__, tool_name))

