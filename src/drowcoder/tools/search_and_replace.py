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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Union

from .base import BaseTool, ToolResponse, ToolResponseMetadata, ToolResponseType, _IntactType


TOOL_NAME = 'search_and_replace'

@dataclass(frozen=True)
class OutputStyle:
    """Output formatting styles"""
    DEFAULT      :str = "default"
    GIT_DIFF     :str = "git_diff"
    GIT_CONFLICT :str = "git_conflict"


@dataclass(frozen=True)
class ExecutionMode:
    """Execution modes"""
    PREVIEW :str = "preview"
    APPLY   :str = "apply"


@dataclass
class LineMatch:
    """Represents a line that matches the search pattern"""
    line_number: int
    original_line: str
    replacement_lines: List[str]


@dataclass
class FileResponse:
    """Response for a single file's search and replace operation."""
    file_path: Path
    matches: List[LineMatch] = field(default_factory=list)

    @property
    def has_matches(self) -> bool:
        return len(self.matches) > 0

    @property
    def total_matches(self) -> int:
        return len(self.matches)


@dataclass
class SearchAndReplaceConfig:
    """Configuration for search and replace operation"""
    file: Union[str, Path]
    search: str
    replace: Union[str, List[str]]
    file_pattern: str = "*"
    case_sensitive: bool = True
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    mode: str = ExecutionMode.APPLY
    output_style: str = OutputStyle.DEFAULT
    output_file: Optional[Union[str, Path]] = None

    def __post_init__(self):
        # Normalize replacement to list of lines
        if isinstance(self.replace, str):
            self.replace = self.replace.split('\n')

@dataclass
class SearchAndReplaceToolResponseMetadata(ToolResponseMetadata, SearchAndReplaceConfig):
    """
    Metadata for search_and_replace tool response.

    Combines ToolResponseMetadata with SearchAndReplaceConfig to provide
    complete context about the search and replace operation.
    """

@dataclass
class SearchAndReplaceToolResponse(ToolResponse):
    """
    Response from search_and_replace tool execution.

    Extends ToolResponse with search_and_replace-specific information.
    Contains file_responses list with per-file match and replacement details.
    """
    tool_name: str = TOOL_NAME
    file_responses: List[FileResponse] = field(default_factory=list)

    @property
    def total_files_with_matches(self) -> int:
        return sum(1 for fr in self.file_responses if fr.has_matches)

    @property
    def total_matches(self) -> int:
        return sum(fr.total_matches for fr in self.file_responses)


class LineSearcher:
    """Handles line-based exact matching"""

    def __init__(self, config: SearchAndReplaceConfig):
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
    def format_default(file_response: FileResponse) -> str:
        """Generate complete modified file content"""
        if not file_response.has_matches:
            # Return original content if no matches
            try:
                with open(file_response.file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return ""

        # Read original content and apply replacements
        try:
            with open(file_response.file_path, 'r', encoding='utf-8') as f:
                lines = f.read().split('\n')
        except:
            return ""

        # Apply replacements from bottom to top to maintain line numbers
        for match in reversed(file_response.matches):
            line_idx = match.line_number - 1

            # Check if this is a multi-line match
            original_lines = match.original_line.split('\n')
            lines_to_replace = len(original_lines)

            if 0 <= line_idx < len(lines):
                # Replace the matched lines with replacement lines
                lines[line_idx:line_idx + lines_to_replace] = match.replacement_lines

        return '\n'.join(lines)

    @staticmethod
    def format_git_diff(file_response: FileResponse) -> str:
        """Generate git diff style output"""
        if not file_response.has_matches:
            return ""

        output = []
        output.append(f"diff --git a/{file_response.file_path} b/{file_response.file_path}")
        output.append("index 0000000..0000000 100644")
        output.append(f"--- a/{file_response.file_path}")
        output.append(f"+++ b/{file_response.file_path}")

        for match in file_response.matches:
            line_num = match.line_number
            output.append(f"@@ -{line_num},1 +{line_num},{len(match.replacement_lines)} @@")
            output.append(f"-{match.original_line}")
            for replacement_line in match.replacement_lines:
                output.append(f"+{replacement_line}")

        return '\n'.join(output)

    @staticmethod
    def format_git_conflict(file_response: FileResponse) -> str:
        """Generate git conflict style output for VS Code rendering"""
        if not file_response.has_matches:
            return OutputFormatter.format_default(file_response)

        try:
            with open(file_response.file_path, 'r', encoding='utf-8') as f:
                lines = f.read().split('\n')
        except:
            return ""

        # Apply conflict markers from bottom to top
        for match in reversed(file_response.matches):
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
        file_pattern: str = "*",
        case_sensitive: bool = True,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        mode: str = ExecutionMode.APPLY,
        output_style: str = OutputStyle.DEFAULT,
        output_file: Optional[Union[str, Path]] = None,
        as_type: Union[str, _IntactType] = ToolResponseType.PRETTY_STR,
        filter_empty_fields: bool = True,
        filter_metadata_fields: bool = True,
    ) -> Any:
        """
        Execute search and replace operation.

        Args:
            file: File or directory to search
            search: Exact line to search for
            replace: Replacement text (can be multiline)
            file_pattern: File pattern to match (default: "*")
            case_sensitive: Whether search is case sensitive (default: True)
            start_line: Start line number for search range (optional)
            end_line: End line number for search range (optional)
            mode: "preview" or "apply"
            output_style: "default", "git_diff", or "git_conflict"
            output_file: Optional output file path (for apply mode)
            as_type: Output format type for the response
            filter_empty_fields: Whether to filter empty fields in output
            filter_metadata_fields: Whether to filter metadata fields in output

        Returns:
            SearchAndReplaceToolResponse (or converted format based on as_type)
        """
        self._validate_initialized()

        local_vars = locals().copy()
        dumping_kwargs = self._parse_dump_kwargs(local_vars)

        try:

            # Create configuration
            kwargs = self._parse_dump_kwargs(local_vars, invert=True)
            if 'self' in kwargs:
                kwargs.pop('self')
            config = SearchAndReplaceConfig(**kwargs)

            # Check if search and replace are identical
            if self._is_search_replace_identical(search, replace):
                self.logger.info("Search and replace patterns are identical - no changes needed.")
                return SearchAndReplaceToolResponse(
                    success=True,
                    file_responses=[],
                    content="No changes needed",
                    metadata=SearchAndReplaceToolResponseMetadata(**config.__dict__)
                ).dump(**dumping_kwargs)

            # Find files to process
            target_path = Path(file)
            files_to_process = self._find_files(target_path, config.file_pattern)

            # Process each file
            file_responses = []
            searcher = LineSearcher(config)
            for file_path in files_to_process:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    matches = searcher.find_matches(content)
                    file_response = FileResponse(file_path=file_path, matches=matches)
                    file_responses.append(file_response)

                except Exception as e:
                    self.logger.warning(f"Error processing {file_path}: {e}")

            response = SearchAndReplaceToolResponse(
                success=True,
                file_responses=file_responses,
                metadata=SearchAndReplaceToolResponseMetadata(**config.__dict__)
            )

            # Normalize mode and output_style to string
            mode_str = mode.lower() if isinstance(mode, str) else mode
            style_str = output_style.lower() if isinstance(output_style, str) else output_style

            # Handle output based on mode
            if mode_str == ExecutionMode.PREVIEW:
                self._handle_preview(response, style_str)
            else:
                self._handle_apply(response, style_str, output_file)

            # Trigger callback if configured
            self._trigger_callback("search_and_replace_completed", {
                "file": str(target_path),
                "total_matches": response.total_matches,
                "files_with_matches": response.total_files_with_matches
            })

            return response.dump(**dumping_kwargs)

        except FileNotFoundError as e:
            # Re-raise FileNotFoundError as is to match original behavior
            self.logger.error(f"File not found: {str(e)}")
            return SearchAndReplaceToolResponse(
                success=False,
                error=f"Path not found: {str(e)}".replace("Path not found: Path not found: ", "Path not found: ")
            ).dump(**dumping_kwargs)
        except Exception as e:
            error_msg = f"Search and replace failed: {str(e)}"
            self.logger.error(error_msg)

            return SearchAndReplaceToolResponse(
                success=False,
                error=error_msg
            ).dump(**dumping_kwargs)

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

    def _handle_preview(self, response: SearchAndReplaceToolResponse, style: str):
        """Handle preview mode output"""
        file_count = 0

        for file_response in response.file_responses:
            if not file_response.has_matches:
                continue

            file_count += 1
            self.logger.info("=" * 60)
            self.logger.info(f"File: {file_response.file_path}")
            self.logger.info(f"Matches: {file_response.total_matches}")
            self.logger.info("=" * 60)

            # Output formatted content
            if style == OutputStyle.DEFAULT:
                formatted_output = self.formatter.format_default(file_response)
            elif style == OutputStyle.GIT_DIFF:
                formatted_output = self.formatter.format_git_diff(file_response)
            elif style == OutputStyle.GIT_CONFLICT:
                formatted_output = self.formatter.format_git_conflict(file_response)
            else:
                formatted_output = ""

            # Log formatted output line by line to preserve formatting
            for line in formatted_output.splitlines():
                self.logger.info(line)

        # Set response content once at the end
        response.content = f"Preview completed: {file_count} files with matches, {response.total_matches} total matches"

    def _handle_apply(self, response: SearchAndReplaceToolResponse, style: str, output_file: Optional[Path]):
        """Handle apply mode output"""
        files_written = []
        errors = []

        for file_response in response.file_responses:
            if not file_response.has_matches:
                continue

            # Determine output path
            if output_file:
                target_path = Path(output_file)
            else:
                target_path = file_response.file_path

            # Generate content based on style
            if style == OutputStyle.DEFAULT:
                content = self.formatter.format_default(file_response)
            elif style == OutputStyle.GIT_DIFF:
                content = self.formatter.format_git_diff(file_response)
                # For git diff, save to .diff file
                target_path = target_path.with_suffix('.diff')
            elif style == OutputStyle.GIT_CONFLICT:
                content = self.formatter.format_git_conflict(file_response)

            # Write to file
            try:
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_written.append(str(target_path))
                self.logger.info(f"Applied changes to: {target_path}")
            except Exception as e:
                error_msg = f"Error writing to {target_path}: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)

        # Set response status once at the end
        if errors:
            response.success = False
            response.error = "; ".join(errors)
            response.content = f"Apply completed with errors: {len(files_written)} succeeded, {len(errors)} failed"
        else:
            response.content = f"Apply completed: {len(files_written)} files written"