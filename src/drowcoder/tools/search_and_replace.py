"""
Refactored search_and_replace tool using unified tool architecture.

This module provides file content search and replace functionality with:
- Exact line matching (single and multi-line)
- Replace operations (one-to-many, many-to-one, deletion)
- Preview and apply modes
- Multiple output styles (default, git_diff, git_conflict)
- Line range targeting
- Case sensitivity control
- Unified tool interface with BaseTool
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union, Any

from .base import BaseTool, ToolResult


class OutputStyle(Enum):
    """Output formatting styles"""
    DEFAULT = "default"
    GIT_DIFF = "git_diff"
    GIT_CONFLICT = "git_conflict"


class ExecutionMode(Enum):
    """Execution modes"""
    PREVIEW = "preview"
    APPLY = "apply"


@dataclass
class LineMatch:
    """Represents a line that matches the search pattern"""
    line_number: int
    original_line: str
    replacement_lines: List[str]


@dataclass
class FileResult:
    """Results for a single file"""
    file_path: Path
    matches: List[LineMatch] = field(default_factory=list)

    @property
    def has_matches(self) -> bool:
        return len(self.matches) > 0

    @property
    def total_matches(self) -> int:
        return len(self.matches)


@dataclass
class SearchReplaceConfig:
    """Configuration for search and replace operation"""
    search: str
    replace: Union[str, List[str]]
    file_pattern: str = "*"
    case_sensitive: bool = True
    start_line: Optional[int] = None
    end_line: Optional[int] = None

    def __post_init__(self):
        # Normalize replacement to list of lines
        if isinstance(self.replace, str):
            self.replace = self.replace.split('\n')


@dataclass
class SearchReplaceResult:
    """Complete search and replace results"""
    config: SearchReplaceConfig
    file_results: List[FileResult] = field(default_factory=list)

    @property
    def total_files_with_matches(self) -> int:
        return sum(1 for fr in self.file_results if fr.has_matches)

    @property
    def total_matches(self) -> int:
        return sum(fr.total_matches for fr in self.file_results)


@dataclass
class SearchReplaceToolResult(ToolResult):
    """
    Result from search_and_replace tool execution.

    Extends ToolResult with search_and_replace-specific information.
    """
    config: Optional[SearchReplaceConfig] = None
    file_results: List[FileResult] = field(default_factory=list)

    @property
    def total_files_with_matches(self) -> int:
        return sum(1 for fr in self.file_results if fr.has_matches)

    @property
    def total_matches(self) -> int:
        return sum(fr.total_matches for fr in self.file_results)


class LineSearcher:
    """Handles line-based exact matching"""

    def __init__(self, config: SearchReplaceConfig):
        self.config = config

    def find_matches(self, content: str) -> List[LineMatch]:
        """Find all matching lines in content"""
        lines = content.split('\n')
        matches = []

        # Determine search range
        start_idx = (self.config.start_line - 1) if self.config.start_line else 0
        end_idx = (self.config.end_line - 1) if self.config.end_line else len(lines) - 1
        start_idx = max(0, start_idx)
        end_idx = min(len(lines) - 1, end_idx)

        # Check if search pattern is multi-line
        search_lines = self.config.search.split('\n')
        is_multiline_search = len(search_lines) > 1

        if is_multiline_search:
            matches = self._find_multiline_matches(lines, search_lines, start_idx, end_idx)
        else:
            matches = self._find_single_line_matches(lines, start_idx, end_idx)

        return matches

    def _find_single_line_matches(self, lines: List[str], start_idx: int, end_idx: int) -> List[LineMatch]:
        """Find single line matches"""
        matches = []
        for i in range(start_idx, end_idx + 1):
            line = lines[i]
            if self._line_matches(line, self.config.search):
                match = LineMatch(
                    line_number=i + 1,
                    original_line=line,
                    replacement_lines=self.config.replace.copy()
                )
                matches.append(match)
        return matches

    def _find_multiline_matches(self, lines: List[str], search_lines: List[str], start_idx: int, end_idx: int) -> List[LineMatch]:
        """Find multi-line matches"""
        matches = []
        search_line_count = len(search_lines)

        # Slide through the lines looking for multi-line matches
        i = start_idx
        while i <= end_idx - search_line_count + 1:
            # Check if the next N lines match the search pattern
            candidate_lines = lines[i:i + search_line_count]
            if len(candidate_lines) == search_line_count and self._multiline_matches(candidate_lines, search_lines):
                # Create a match that represents multiple lines
                original_content = '\n'.join(candidate_lines)
                match = LineMatch(
                    line_number=i + 1,  # Start line number
                    original_line=original_content,  # Store all matched lines
                    replacement_lines=self.config.replace.copy()
                )
                matches.append(match)

                # Skip the matched lines to avoid overlapping matches
                i += search_line_count
            else:
                i += 1

        return matches

    def _multiline_matches(self, candidate_lines: List[str], search_lines: List[str]) -> bool:
        """Check if multiple lines match the search pattern"""
        if len(candidate_lines) != len(search_lines):
            return False

        for candidate_line, search_line in zip(candidate_lines, search_lines):
            if not self._line_matches(candidate_line, search_line):
                return False
        return True

    def _line_matches(self, line: str, search: str) -> bool:
        """Check if a line matches the search pattern"""
        # For exact line matching, we compare the stripped versions
        line_to_check = line.strip()
        search_to_check = search.strip()

        if not self.config.case_sensitive:
            return search_to_check.lower() == line_to_check.lower()
        return search_to_check == line_to_check


class OutputFormatter:
    """Handles different output formatting styles"""

    @staticmethod
    def format_default(file_result: FileResult) -> str:
        """Generate complete modified file content"""
        if not file_result.has_matches:
            # Return original content if no matches
            try:
                with open(file_result.file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return ""

        # Read original content and apply replacements
        try:
            with open(file_result.file_path, 'r', encoding='utf-8') as f:
                lines = f.read().split('\n')
        except:
            return ""

        # Apply replacements from bottom to top to maintain line numbers
        for match in reversed(file_result.matches):
            line_idx = match.line_number - 1

            # Check if this is a multi-line match
            original_lines = match.original_line.split('\n')
            lines_to_replace = len(original_lines)

            if 0 <= line_idx < len(lines):
                # Replace the matched lines with replacement lines
                lines[line_idx:line_idx + lines_to_replace] = match.replacement_lines

        return '\n'.join(lines)

    @staticmethod
    def format_git_diff(file_result: FileResult) -> str:
        """Generate git diff style output"""
        if not file_result.has_matches:
            return ""

        output = []
        output.append(f"diff --git a/{file_result.file_path} b/{file_result.file_path}")
        output.append("index 0000000..0000000 100644")
        output.append(f"--- a/{file_result.file_path}")
        output.append(f"+++ b/{file_result.file_path}")

        for match in file_result.matches:
            line_num = match.line_number
            output.append(f"@@ -{line_num},1 +{line_num},{len(match.replacement_lines)} @@")
            output.append(f"-{match.original_line}")
            for replacement_line in match.replacement_lines:
                output.append(f"+{replacement_line}")

        return '\n'.join(output)

    @staticmethod
    def format_git_conflict(file_result: FileResult) -> str:
        """Generate git conflict style output for VS Code rendering"""
        if not file_result.has_matches:
            return OutputFormatter.format_default(file_result)

        try:
            with open(file_result.file_path, 'r', encoding='utf-8') as f:
                lines = f.read().split('\n')
        except:
            return ""

        # Apply conflict markers from bottom to top
        for match in reversed(file_result.matches):
            line_idx = match.line_number - 1

            # Check if this is a multi-line match
            original_lines = match.original_line.split('\n')
            lines_to_replace = len(original_lines)

            if 0 <= line_idx < len(lines):
                conflict_block = ["<<<<<<< HEAD"] + original_lines + ["======="] + match.replacement_lines + [">>>>>>> incoming"]
                lines[line_idx:line_idx + lines_to_replace] = conflict_block

        return '\n'.join(lines)


class SearchAndReplaceTool(BaseTool):
    """
    Tool for searching and replacing content in files.

    Supports exact line matching, multi-line patterns,
    various output styles, and preview/apply modes.
    """
    name = 'search_and_replace'

    def __init__(self, **kwargs):
        """Initialize SearchAndReplaceTool."""
        super().__init__(**kwargs)
        self.formatter = OutputFormatter()

    def execute(
        self,
        file: Union[str, Path],
        search: str,
        replace: Union[str, List[str]],
        mode: str = "apply",
        output_style: str = "default",
        output_file: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> SearchReplaceToolResult:
        """
        Execute search and replace operation.

        Args:
            file: File or directory to search
            search: Exact line to search for
            replace: Replacement text (can be multiline)
            mode: "preview" or "apply"
            output_style: "default", "git_diff", or "git_conflict"
            output_file: Optional output file path (for apply mode)
            **kwargs: Additional configuration options (case_sensitive, start_line, end_line, file_pattern)

        Returns:
            SearchReplaceToolResult with operation results
        """
        self._validate_initialized()

        try:
            # Check if search and replace are identical
            if self._is_search_replace_identical(search, replace):
                print("ℹ️  Search and replace patterns are identical - no changes needed.")
                config = SearchReplaceConfig(search=search, replace=replace, **kwargs)
                return SearchReplaceToolResult(
                    success=True,
                    config=config,
                    file_results=[],
                    data="No changes needed"
                )

            # Create configuration
            config = SearchReplaceConfig(
                search=search,
                replace=replace,
                **kwargs
            )

            # Find files to process
            target_path = Path(file)
            files_to_process = self._find_files(target_path, config.file_pattern)

            # Process each file
            result = SearchReplaceToolResult(config=config, success=True)
            searcher = LineSearcher(config)

            for file_path in files_to_process:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    matches = searcher.find_matches(content)
                    file_result = FileResult(file_path=file_path, matches=matches)
                    result.file_results.append(file_result)

                except Exception as e:
                    self.logger.warning(f"Error processing {file_path}: {e}")

            # Handle output based on mode
            execution_mode = ExecutionMode(mode.lower())
            style = OutputStyle(output_style.lower())

            if execution_mode == ExecutionMode.PREVIEW:
                self._handle_preview(result, style)
                result.data = "Preview completed"
            else:  # APPLY
                self._handle_apply(result, style, output_file)
                result.data = "Apply completed"

            # Trigger callback if configured
            self._trigger_callback("search_and_replace_completed", {
                "file": str(target_path),
                "total_matches": result.total_matches,
                "files_with_matches": result.total_files_with_matches
            })

            self.logger.info(f"Search and replace completed: {result.total_matches} matches in {result.total_files_with_matches} files")

            return result

        except FileNotFoundError as e:
            # Re-raise FileNotFoundError as is to match original behavior
            self.logger.error(f"File not found: {str(e)}")
            return SearchReplaceToolResult(
                success=False,
                error=f"Path not found: {str(e)}".replace("Path not found: Path not found: ", "Path not found: ")
            )
        except Exception as e:
            error_msg = f"Search and replace failed: {str(e)}"
            self.logger.error(error_msg)

            return SearchReplaceToolResult(
                success=False,
                error=error_msg
            )

    def _is_search_replace_identical(self, search: str, replace: Union[str, List[str]]) -> bool:
        """Check if search and replace patterns are identical"""
        # Normalize replace to string
        if isinstance(replace, list):
            replace_str = '\n'.join(replace)
        else:
            replace_str = replace

        # Compare normalized patterns
        return search.strip() == replace_str.strip()

    def _find_files(self, target_path: Path, pattern: str) -> List[Path]:
        """Find files matching the pattern"""
        if target_path.is_file():
            return [target_path]

        if target_path.is_dir():
            return list(target_path.rglob(pattern))

        raise FileNotFoundError(f"Path not found: {target_path}")

    def _handle_preview(self, result: SearchReplaceToolResult, style: OutputStyle):
        """Handle preview mode output"""
        for file_result in result.file_results:
            if not file_result.has_matches:
                continue

            print(f"\n{'='*60}")
            print(f"File: {file_result.file_path}")
            print(f"Matches: {file_result.total_matches}")
            print('='*60)

            if style == OutputStyle.DEFAULT:
                print(self.formatter.format_default(file_result))
            elif style == OutputStyle.GIT_DIFF:
                print(self.formatter.format_git_diff(file_result))
            elif style == OutputStyle.GIT_CONFLICT:
                print(self.formatter.format_git_conflict(file_result))

    def _handle_apply(self, result: SearchReplaceToolResult, style: OutputStyle, output_file: Optional[Path]):
        """Handle apply mode output"""
        for file_result in result.file_results:
            if not file_result.has_matches:
                continue

            # Determine output path
            if output_file:
                target_path = Path(output_file)
            else:
                target_path = file_result.file_path

            # Generate content based on style
            if style == OutputStyle.DEFAULT:
                content = self.formatter.format_default(file_result)
            elif style == OutputStyle.GIT_DIFF:
                content = self.formatter.format_git_diff(file_result)
                # For git diff, save to .diff file
                target_path = target_path.with_suffix('.diff')
            elif style == OutputStyle.GIT_CONFLICT:
                content = self.formatter.format_git_conflict(file_result)

            # Write to file
            try:
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Applied changes to: {target_path}")
            except Exception as e:
                self.logger.error(f"Error writing to {target_path}: {e}")
                result.success = False


# Backward compatible function interface
def search_and_replace(
    file: Union[str, Path],
    search: str,
    replace: Union[str, List[str]],
    mode: str = "apply",
    output_style: str = "default",
    output_file: Optional[Union[str, Path]] = None,
    **kwargs
) -> SearchReplaceResult:
    """
    Search for specific text patterns in files and replace them with new content.

    This is a backward-compatible wrapper around SearchAndReplaceTool.
    Preserves the exact interface and behavior of the original function.

    Features:
    - One-to-many: single line → multiple lines
    - Many-to-one: multiple lines → single line
    - Deletion: replace with empty string ""
    - Line range targeting with start_line/end_line

    Args:
        file: Target file or directory path
        search: Exact line(s) to find. Use '\\n' for consecutive multi-line patterns
        replace: Replacement content. Empty string "" for deletion
        mode: Execution mode options:
            - "preview": Show changes without modifying files
            - "apply": Apply changes directly to files
            - "preview_and_ask": Preview first, then ask for confirmation
        output_style: Output formatting style:
            - "default": Complete modified file content
            - "git_diff": Git diff style output
            - "git_conflict": Git conflict markers (VS Code compatible)
        output_file: Custom output path (None = modify original)
        **kwargs: Additional options:
            - case_sensitive (bool): Case sensitive search (default: True)
            - start_line (int): Start line number (1-based)
            - end_line (int): End line number (1-based)
            - file_pattern (str): File pattern for directory search (default: "*")

    Returns:
        SearchReplaceResult: Results with match statistics and file info

    Raises:
        ValueError: If invalid mode is specified
        FileNotFoundError: If target file/directory doesn't exist

    Examples:
        # Basic replacement
        search_and_replace("file.txt", "old line", "new line")

        # Preview mode
        search_and_replace("file.txt", "old line", "new line", mode="preview")

        # Interactive (preview and ask) mode with confirmation
        search_and_replace("file.txt", "old line", "new line", mode="preview_and_ask")

        # Delete lines
        search_and_replace("file.txt", "unwanted line", "", mode="apply")

        # One to many replacement
        search_and_replace("file.txt", "TODO", "Step 1\\nStep 2\\nStep 3", mode="apply")

        # Many to one replacement
        search_and_replace("file.txt", "Line 1\\nLine 2", "Single line", mode="apply")

        # With git conflict style for VS Code
        search_and_replace("file.txt", "old", "new", output_style="git_conflict")

        # Case insensitive with line range
        search_and_replace("file.txt", "OLD", "new", case_sensitive=False,
                          start_line=10, end_line=50)
    """
    # Validate mode parameter
    valid_modes = ["preview", "apply", "preview_and_ask"]
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}")

    # Handle interactive (preview and ask) mode
    if mode == "preview_and_ask":
        return search_and_ask_replace(
            file=file,
            search=search,
            replace=replace,
            output_style=output_style,
            output_file=output_file,
            **kwargs
        )

    # Handle standard preview/apply modes
    tool = SearchAndReplaceTool()
    tool_result = tool.execute(
        file=file,
        search=search,
        replace=replace,
        mode=mode,
        output_style=output_style,
        output_file=output_file,
        **kwargs
    )

    # Convert ToolResult to SearchReplaceResult for backward compatibility
    if tool_result.success:
        return SearchReplaceResult(
            config=tool_result.config,
            file_results=tool_result.file_results
        )
    else:
        # On error, raise appropriate exception to match original behavior
        if "Path not found" in tool_result.error:
            # Extract the path from error message
            path = tool_result.error.replace("Path not found: ", "")
            raise FileNotFoundError(f"Path not found: {path}")
        else:
            raise RuntimeError(tool_result.error)


def search_and_ask_replace(
    file: Union[str, Path],
    search: str,
    replace: Union[str, List[str]],
    output_style: str = "default",
    output_file: Optional[Union[str, Path]] = None,
    **kwargs
) -> Union[SearchReplaceResult, str]:
    """
    Interactive search and replace - preview first, then ask for confirmation.

    This function first shows a preview of all changes that would be made,
    then prompts the user for confirmation before applying them.

    Args:
        file: Target file or directory path to search in
        search: Exact line(s) to find. Use '\\n' for consecutive multi-line patterns
        replace: Replacement content. Can be multiline string or empty string for deletion
        output_style: Output formatting style:
            - "default": Complete modified file content
            - "git_diff": Git diff style output
            - "git_conflict": Git conflict markers (VS Code compatible)
        output_file: Custom output path (None = modify original file)
        **kwargs: Additional options:
            - case_sensitive (bool): Case sensitive search (default: True)
            - start_line (int): Start line number for search range (1-based)
            - end_line (int): End line number for search range (1-based)
            - file_pattern (str): File pattern for directory search (default: "*")

    Returns:
        Union[SearchReplaceResult, str]:
            - SearchReplaceResult if changes are applied or no matches found
            - str with cancellation message if user declines or interrupts

    User Interaction:
        - Shows preview of changes with match statistics
        - Prompts: "Apply these changes? (y [YES] | n [NO]): "
        - Accepts: 'y', 'yes', 'true', 'apply' to confirm
        - Accepts: 'n', 'no', 'false', 'cancel' to decline
        - Handles Ctrl+C and EOF gracefully

    Examples:
        # Basic interactive (preview and ask) replacement
        result = search_and_ask_replace("file.txt", "old line", "new line")

        # With git conflict style
        result = search_and_ask_replace("file.txt", "old", "new",
                                       output_style="git_conflict")

        # Multi-line replacement with confirmation
        result = search_and_ask_replace("file.txt", "TODO\\nFIXME",
                                       "COMPLETED\\nDONE")
    """
    tool = SearchAndReplaceTool()
    tool_result = tool.execute(
        file=file,
        search=search,
        replace=replace,
        mode='preview',
        output_style=output_style,
        output_file=output_file,
        **kwargs
    )

    # Convert to SearchReplaceResult
    preview_result = SearchReplaceResult(
        config=tool_result.config,
        file_results=tool_result.file_results
    )

    # Check if any matches were found
    if preview_result.total_matches == 0:
        print("❌ No matches found.")
        return preview_result

    print(f"\n📊 Found {preview_result.total_matches} match(es) in {preview_result.total_files_with_matches} file(s)")
    print("=" * 60)

    # Ask for confirmation
    while True:
        try:
            permission = input("Apply these changes? (y[YES]|n[NO]): ").strip()

            if permission.lower() in ['y', 'yes', 'true', 'apply']:
                apply_tool_result = tool.execute(
                    file=file,
                    search=search,
                    replace=replace,
                    mode='apply',
                    output_style=output_style,
                    output_file=output_file,
                    **kwargs
                )
                # Convert to SearchReplaceResult
                return SearchReplaceResult(
                    config=apply_tool_result.config,
                    file_results=apply_tool_result.file_results
                )
            elif permission.lower() in ['n', 'no', 'false', 'cancel']:
                message = "❌ Changes cancelled by user."
                return message
            else:
                print("❓ Please enter 'Y'/'yes' to apply or 'N'/'no' to cancel.")
                continue
        except KeyboardInterrupt:
            message = "\n❌ Operation cancelled by user (Ctrl+C)."
            return message
        except EOFError:
            message = "\n❌ Operation cancelled (EOF)."
            return message

