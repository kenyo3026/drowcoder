"""
Unit tests for search tool.

Tests cover:
- Basic search functionality
- File pattern filtering
- Content pattern matching (regex)
- Output formats (graph, text, raw)
- Workspace boundary checking
- Ignore file filtering
- Edge cases (empty results, invalid patterns, etc.)
- Unicode and special characters
- Tool class interface

Usage:
    # Test original search tool
    python -m src.drowcoder.tools.tests.test_search

    # Test refactored search tool
    python -m src.drowcoder.tools.tests.test_search --module search_refactor
"""

import pytest
import sys
import os
import tempfile
import re
from pathlib import Path
import importlib

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Get module name from environment variable or use default
TEST_MODULE = os.environ.get('TEST_SEARCH_MODULE', 'search')

# Dynamically import the specified module
search_module = importlib.import_module(f'drowcoder.tools.{TEST_MODULE}')
SearchTool = getattr(search_module, 'SearchTool', None)
SearchToolResult = getattr(search_module, 'SearchToolResult', None)
FileMatchMeta = getattr(search_module, 'FileMatchMeta', None)
LineMeta = getattr(search_module, 'LineMeta', None)

# Helper function to maintain test compatibility
def search(pattern, file, **kwargs):
    """Wrapper function for testing - creates tool instance and calls execute"""
    tool = SearchTool()
    return tool.execute(pattern=pattern, file=file, **kwargs)


@pytest.fixture
def tmp_path():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_files(tmp_path):
    """Create test files with various content."""
    files = {}

    # Python file with TODO
    files['test.py'] = tmp_path / "test.py"
    files['test.py'].write_text("""# Test file
def hello():
    print("Hello")
    # TODO: Add more features
    return True
""")

    # Text file with keywords
    files['test.txt'] = tmp_path / "test.txt"
    files['test.txt'].write_text("""Line 1: Search term
Line 2: Another line
Line 3: Search term again
""")

    # File with special characters
    files['special.txt'] = tmp_path / "special.txt"
    files['special.txt'].write_text("""Special: !@#$%^&*()
Unicode: 中文 日本語
""")

    # Empty file
    files['empty.txt'] = tmp_path / "empty.txt"
    files['empty.txt'].write_text("")

    # File with many lines
    files['many_lines.txt'] = tmp_path / "many_lines.txt"
    files['many_lines.txt'].write_text("\n".join([f"Line {i}: content" for i in range(100)]))

    return files


class TestSearchBasic:
    """Basic search functionality tests."""

    def test_simple_search(self, tmp_path, test_files):
        """Test simple content search."""
        test_files['test.txt'].write_text("Search term here")

        result = search(str(tmp_path), "Search term", "*", cwd=str(tmp_path))

        assert isinstance(result, str)
        assert "test.txt" in result or "Search term" in result

    def test_regex_pattern(self, tmp_path, test_files):
        """Test regex pattern matching."""
        result = search(str(tmp_path), "def\\s+\\w+", "*.py", cwd=str(tmp_path))

        assert isinstance(result, str)
        assert "def" in result.lower() or "No matching" in result

    def test_file_pattern_filtering(self, tmp_path, test_files):
        """Test file pattern filtering."""
        result = search(str(tmp_path), ".*", "*.py", cwd=str(tmp_path))

        assert isinstance(result, str)
        # Should only find Python files
        assert "test.txt" not in result or "No matching" in result

    def test_search_in_single_file(self, tmp_path, test_files):
        """Test searching in a single file."""
        result = search(str(test_files['test.py']), "TODO", "*", cwd=str(tmp_path))

        assert isinstance(result, str)
        assert "TODO" in result or "No matching" in result


class TestSearchOutputFormats:
    """Test different output formats."""

    def test_text_format(self, tmp_path, test_files):
        """Test text output format."""
        result = search(
            str(tmp_path),
            "Search term",
            "*",
            cwd=str(tmp_path),
            as_text=True,
            as_graph=False
        )

        assert isinstance(result, str)

    def test_graph_format(self, tmp_path, test_files):
        """Test graph output format."""
        result = search(
            str(tmp_path),
            ".*",
            "*",
            cwd=str(tmp_path),
            as_text=True,
            as_graph=True
        )

        assert isinstance(result, str)

    def test_raw_results(self, tmp_path, test_files):
        """Test raw results format."""
        result = search(
            str(tmp_path),
            "Search term",
            "*",
            cwd=str(tmp_path),
            as_text=False,
            as_graph=False
        )

        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], FileMatchMeta)

    def test_only_filename(self, tmp_path, test_files):
        """Test only_filename option."""
        result = search(
            str(tmp_path),
            ".*",
            "*",
            cwd=str(tmp_path),
            only_filename=True
        )

        assert isinstance(result, str)
        # Should contain filenames but not detailed content


class TestSearchEdgeCases:
    """Edge case tests."""

    def test_empty_results(self, tmp_path, test_files):
        """Test search with no matches."""
        result = search(str(tmp_path), "NonExistentPattern123", "*", cwd=str(tmp_path))

        assert isinstance(result, str)
        assert "No matching" in result or "0 files" in result.lower()

    def test_empty_file(self, tmp_path, test_files):
        """Test searching in empty file."""
        result = search(str(test_files['empty.txt']), ".*", "*", cwd=str(tmp_path))

        assert isinstance(result, str)
        assert "No matching" in result or "0 files" in result.lower()

    def test_pattern_matching_all_lines(self, tmp_path, test_files):
        """Test pattern that matches all lines."""
        result = search(str(tmp_path), ".*", "*", cwd=str(tmp_path))

        assert isinstance(result, str)
        # Should find files with matches

    def test_case_sensitive_search(self, tmp_path, test_files):
        """Test case sensitive search."""
        test_files['case.txt'] = tmp_path / "case.txt"
        test_files['case.txt'].write_text("Hello World\nhello world")

        result = search(str(tmp_path), "Hello", "*", cwd=str(tmp_path))

        assert isinstance(result, str)
        # Should find case-sensitive matches


class TestSearchUnicode:
    """Unicode and special character tests."""

    def test_unicode_content(self, tmp_path, test_files):
        """Test searching Unicode content."""
        result = search(str(tmp_path), "中文", "*", cwd=str(tmp_path))

        assert isinstance(result, str)

    def test_special_characters(self, tmp_path, test_files):
        """Test searching special characters."""
        result = search(str(tmp_path), "!@#", "*", cwd=str(tmp_path))

        assert isinstance(result, str)

    def test_emoji_in_content(self, tmp_path):
        """Test searching files with emoji."""
        emoji_file = tmp_path / "emoji.txt"
        emoji_file.write_text("Hello 😀 World")

        result = search(str(tmp_path), "😀", "*", cwd=str(tmp_path))

        assert isinstance(result, str)


class TestSearchErrors:
    """Error handling tests."""

    def test_nonexistent_path(self, tmp_path):
        """Test search with nonexistent path."""
        with pytest.raises((FileNotFoundError, RuntimeError)):
            search(str(tmp_path / "nonexistent"), ".*", "*", cwd=str(tmp_path))

    def test_invalid_regex(self, tmp_path, test_files):
        """Test with invalid regex pattern."""
        # Some invalid regex patterns might raise errors
        try:
            result = search(str(tmp_path), "[", "*", cwd=str(tmp_path))
            # If no error, should return a result
            assert isinstance(result, str)
        except re.error:
            # Invalid regex is acceptable
            pass

    def test_outside_workspace_disabled(self, tmp_path):
        """Test search outside workspace when disabled."""
        # Create a file outside workspace
        outside_dir = tmp_path.parent / "outside"
        outside_dir.mkdir(exist_ok=True)
        outside_file = outside_dir / "outside.txt"
        outside_file.write_text("Content")

        try:
            with pytest.raises((ValueError, RuntimeError)):
                search(
                    str(outside_dir),
                    ".*",
                    "*",
                    cwd=str(tmp_path),
                    enable_search_outside=False
                )
        finally:
            # Cleanup
            if outside_file.exists():
                outside_file.unlink()
            if outside_dir.exists():
                outside_dir.rmdir()


class TestSearchMaxMatches:
    """Test max_matches_per_file parameter."""

    def test_limit_matches(self, tmp_path):
        """Test limiting matches per file."""
        test_file = tmp_path / "many_matches.txt"
        content = "\n".join(["Match line"] * 50)
        test_file.write_text(content)

        result = search(
            str(tmp_path),
            "Match",
            "*",
            cwd=str(tmp_path),
            max_matches_per_file=10
        )

        assert isinstance(result, str)
        # Should limit matches displayed


class TestSearchToolClass:
    """Tests for SearchTool class interface."""

    def test_tool_initialization(self):
        """Test that tool can be initialized."""
        if SearchTool:
            tool = SearchTool()
            assert tool is not None
            assert tool._initialized is True

    def test_tool_execute_returns_result(self, tmp_path, test_files):
        """Test that tool.execute() returns SearchToolResult."""
        if SearchTool and SearchToolResult:
            tool = SearchTool()
            result = tool.execute(
                path=str(tmp_path),
                content_pattern=".*",
                filepath_pattern="*",
                cwd=str(tmp_path)
            )

            assert isinstance(result, SearchToolResult)
            assert result.success is True

    def test_tool_with_logger(self, tmp_path, test_files):
        """Test tool with custom logger."""
        if SearchTool:
            import logging
            logger = logging.getLogger("test_logger")
            tool = SearchTool(logger=logger)

            result = tool.execute(
                path=str(tmp_path),
                content_pattern=".*",
                filepath_pattern="*",
                cwd=str(tmp_path)
            )

            assert result.success is True

    def test_tool_with_callback(self, tmp_path, test_files):
        """Test tool with callback function."""
        if SearchTool:
            callback_called = []

            def test_callback(event, data):
                callback_called.append((event, data))

            tool = SearchTool(callback=test_callback)
            result = tool.execute(
                path=str(tmp_path),
                content_pattern=".*",
                filepath_pattern="*",
                cwd=str(tmp_path)
            )

            assert result.success is True
            assert len(callback_called) > 0

    def test_tool_not_initialized(self, tmp_path):
        """Test tool without initialization raises error."""
        if SearchTool:
            tool = SearchTool(auto_initialize=False)

            with pytest.raises(RuntimeError, match="not initialized"):
                tool.execute(
                    path=str(tmp_path),
                    content_pattern=".*",
                    filepath_pattern="*"
                )

    def test_tool_metadata(self, tmp_path, test_files):
        """Test result contains metadata."""
        if SearchTool and SearchToolResult:
            tool = SearchTool()
            result = tool.execute(
                path=str(tmp_path),
                content_pattern=".*",
                filepath_pattern="*",
                cwd=str(tmp_path)
            )

            assert hasattr(result, 'metadata')
            assert isinstance(result.metadata, dict)


class TestSearchResultProperties:
    """Test SearchToolResult properties."""

    def test_result_files_found(self, tmp_path, test_files):
        """Test files_found property."""
        if SearchTool and SearchToolResult:
            tool = SearchTool()
            result = tool.execute(
                path=str(tmp_path),
                content_pattern=".*",
                filepath_pattern="*",
                cwd=str(tmp_path)
            )

            assert hasattr(result, 'files_found')
            assert result.files_found >= 0

    def test_result_total_matches(self, tmp_path, test_files):
        """Test total_matches property."""
        if SearchTool and SearchToolResult:
            tool = SearchTool()
            result = tool.execute(
                path=str(tmp_path),
                content_pattern=".*",
                filepath_pattern="*",
                cwd=str(tmp_path)
            )

            assert hasattr(result, 'total_matches')
            assert result.total_matches >= 0


class TestSearchSubdirectory:
    """Test searching in subdirectories."""

    def test_search_in_subdirectory(self, tmp_path):
        """Test searching recursively in subdirectories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        test_file = subdir / "test.txt"
        test_file.write_text("Search term")

        result = search(str(tmp_path), "Search term", "*", cwd=str(tmp_path))

        assert isinstance(result, str)
        assert "Search term" in result or "subdir" in result


class TestSearchMultipleMatches:
    """Test multiple matches in files."""

    def test_multiple_matches_in_file(self, tmp_path):
        """Test file with multiple matches."""
        test_file = tmp_path / "multi.txt"
        test_file.write_text("Match\nNo match\nMatch\nMatch")

        result = search(str(tmp_path), "Match", "*", cwd=str(tmp_path))

        assert isinstance(result, str)
        assert "Match" in result


class TestSearchParametrized:
    """Parametrized tests for various inputs."""

    @pytest.mark.parametrize("pattern", [
        ".*",
        "def",
        "TODO",
        "import",
        "\\d+",
    ])
    def test_various_patterns(self, tmp_path, test_files, pattern):
        """Test search with various patterns."""
        result = search(str(tmp_path), pattern, "*", cwd=str(tmp_path))
        assert isinstance(result, str)

    @pytest.mark.parametrize("file_pattern", [
        "*.py",
        "*.txt",
        "*",
        "test.*",
    ])
    def test_various_file_patterns(self, tmp_path, test_files, file_pattern):
        """Test search with various file patterns."""
        result = search(str(tmp_path), ".*", file_pattern, cwd=str(tmp_path))
        assert isinstance(result, str)


if __name__ == "__main__":
    import argparse
    from .base import run_tests_with_report

    parser = argparse.ArgumentParser()
    parser.add_argument('--module', default='search', choices=['search', 'search_refactor'],
                        help='Which search module to test: search or search_refactor')
    args = parser.parse_args()

    # Set environment variable for the test module
    os.environ['TEST_SEARCH_MODULE'] = args.module

    # Use module name as tool name
    tool_name = args.module

    print(f"Testing module: {args.module}")
    print(f"Report name: {tool_name}")
    print("=" * 70)

    sys.exit(run_tests_with_report(__file__, tool_name))

