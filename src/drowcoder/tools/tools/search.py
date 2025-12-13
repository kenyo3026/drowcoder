"""
Refactored search tool using unified tool architecture.

This module provides file content search functionality with:
- Regex pattern matching in file contents
- File pattern filtering (glob patterns)
- Workspace boundary checking
- Tree graph and text output formats
- Unified tool interface with BaseTool
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Union

from path_tree_graph import PathTree, PathTreeNode, TreeGraph

from .base import BaseTool, ToolResponse, ToolResponseMetadata, ToolResponseType, _IntactType
from .utils.ext import EXT_PATTERNS_FOR_BASE_EXCLUDE
from .utils.ignore import IgnoreController


TOOL_NAME = 'search'

@dataclass
class LineMeta:
    """
    Represents a single line match in a file.

    Attributes:
        line (int): The line number where the match was found (1-indexed)
        text (str): The stripped text content of the matching line
    """
    line: int
    text: str


@dataclass
class FileMatchMeta:
    """
    Represents a file with search matches.

    Attributes:
        file (str): The absolute file path
        matches (List[LineMeta]): List of line matches found in the file
        total_lines (int): Total number of lines in the file
    """
    file: str
    matches: List[LineMeta]
    total_lines: int

    def format_matches(self, prefix: str = '', max_matches_per_file: int = 10) -> str:
        """
        Format the matches as a readable string with line numbers and content.

        Args:
            prefix (str): Prefix string to add before each line for indentation
            max_matches_per_file (int): Maximum number of matches to display per file

        Returns:
            str: Formatted string representation of the matches
        """
        formatted_str = ''
        for i, match in enumerate(self.matches, 1):
            formatted_str += f"{prefix}  {match.line:<3d} | {match.text}\n"
            if i >= max_matches_per_file:
                break

        if len(self.matches) > max_matches_per_file:
            remaining = len(self.matches) - max_matches_per_file
            formatted_str += f"{prefix}  ... [Content truncated - {remaining} more matches hidden]\n"

        return formatted_str


class PathTreeNodeForSearchTool(PathTreeNode):
    """
    Extended PathTreeNode that can store search result metadata.

    Inherits from PathTreeNode and adds metadata storage capability for search results.
    """

    def __init__(self, name, is_leaf=False, meta:dict=None):
        """
        Initialize a PathTreeNodeForSearchTool.

        Args:
            name (str): The name of this node (directory or file name)
            is_leaf (bool): Whether this node represents a file (leaf) or directory
            meta (dict, optional): Metadata dictionary, typically contains FileMatchMeta
        """
        super().__init__(name=name, is_leaf=is_leaf)
        self.meta = meta or {}

    def add_child(self, child_name, is_leaf=False, meta:dict=None):
        """
        Add a child node to this node.

        Args:
            child_name (str): The name of the child node
            is_leaf (bool): Whether the child node is a leaf (file)
            meta (dict, optional): Metadata for the child node

        Returns:
            PathTreeNodeForSearchTool: The child node (existing or newly created)
        """
        if child_name not in self.children:
            self.children[child_name] = PathTreeNodeForSearchTool(child_name, is_leaf, meta or {})
        return self.children[child_name]


class PathTreeForSearchTool(PathTree):
    """
    Extended PathTree for displaying search results in a tree structure.

    This class extends the base PathTree to work with FileMatchMeta objects
    and provides specialized formatting for search results.
    """

    def add_path(self, path_meta:FileMatchMeta):
        """
        Add a file path with search results to the tree.

        Args:
            path_meta (FileMatchMeta): File metadata containing path and search matches
        """
        path_parts = path_meta.file
        if self.root is None:
            self.root = PathTreeNodeForSearchTool(path_parts[0])

        current_node = self.root
        if path_parts[0] == self.root.name:
            path_parts = path_parts[1:]

        for i, part in enumerate(path_parts):
            is_leaf = (i == len(path_parts) - 1)
            if is_leaf:
                current_node = current_node.add_child(part, is_leaf, meta=path_meta)
            else:
                current_node = current_node.add_child(part, is_leaf)

    def format(
        self,
        node=None,
        prefix="",
        only_filename:bool=False,
        max_matches_per_file:int=10,
    ):
        """
        Format the tree as a string with search results.

        Args:
            node (PathTreeNodeForSearchTool, optional): Starting node (defaults to root)
            prefix (str): Prefix for indentation
            only_filename (bool): If True, only show filenames without match content
            max_matches_per_file (int): Maximum matches to display per file

        Returns:
            str: Formatted tree structure with search results
        """
        if node is None:
            node = self.root

        # Build the tree line
        tree_symbol = "└── " if prefix else ""
        formatted_str = prefix + tree_symbol + node.name + "\n"

        if not only_filename and node.is_leaf and node.meta:
            formatted_str += node.meta.format_matches(
                prefix + " " * len(tree_symbol),
                max_matches_per_file,
            )

        children = sorted(node.children.values(), key=lambda x: x.name)
        for i, child in enumerate(children):
            formatted_str += self.format(
                child,
                prefix + "    ",
                only_filename,
                max_matches_per_file,
            )
        return formatted_str


class TreeGraphForSearchTool(TreeGraph):
    """
    Tree graph specialized for search results visualization.

    This class creates tree structures from search results and provides
    methods to display them in a hierarchical format.
    """
    graph_tree = PathTreeForSearchTool

    @classmethod
    def from_paths(
        cls,
        paths:List[FileMatchMeta],
        concentrate:bool=True,
    ):
        """
        Create a tree graph from a list of file search results.

        Args:
            paths (List[FileMatchMeta]): List of file search results
            concentrate (bool): Whether to compress single-child directory chains

        Returns:
            PathTreeForSearchTool: Tree structure containing the search results
        """
        tree = cls.graph_tree()
        for path_meta in paths:
            path = path_meta.file
            if isinstance(path, str):
                path_meta.file = list(Path(path).parts)
            tree.add_path(path_meta)

        if concentrate:
            tree.root.concentrate()

        return tree


@dataclass
class SearchToolResponseMetadata(ToolResponseMetadata):
    """
    Metadata for search tool response.

    Attributes:
        path: The search path
        content_pattern: The content pattern used for searching
        filepath_pattern: The file pattern used for filtering
        files_found: Number of files that matched the search
        total_matches: Total number of matches across all files
    """
    path: str
    content_pattern: str
    filepath_pattern: str
    files_found: Union[int] = None
    total_matches: Union[int] = None


@dataclass
class SearchToolResponse(ToolResponse):
    """
    Response from search tool execution.

    Extends ToolResponse with search-specific information.
    The content field contains formatted search results.
    """
    tool_name: str = TOOL_NAME


class SearchTool(BaseTool):
    """
    Tool for searching content patterns in files.

    Supports regex pattern matching, file pattern filtering,
    workspace boundary checking, and multiple output formats.
    """
    name = TOOL_NAME

    def execute(
        self,
        path: str,
        content_pattern: str,
        filepath_pattern: str = "*",
        cwd: Optional[str] = None,
        max_matches_per_file: int = 10,
        enable_search_outside: bool = True,
        as_text: bool = True,
        as_graph: bool = True,
        only_filename: bool = False,
        enable_ignore: bool = True,
        shell_policy: str = "auto",
        as_type: Union[str, _IntactType] = ToolResponseType.PRETTY_STR,
        filter_empty_fields: bool = True,
        filter_metadata_fields: bool = False,
    ) -> Any:
        """
        Execute search operation.

        Args:
            path: Directory or file path to search
            content_pattern: Regex pattern to search for in file contents
            filepath_pattern: File pattern to match (e.g., "*.py", "*.txt")
            cwd: Working directory (workspace root). Defaults to current directory
            max_matches_per_file: Maximum number of matches to display per file
            enable_search_outside: Allow searching outside workspace
            as_text: Return formatted text or raw results when as_graph=False
            as_graph: Use tree graph format for displaying results (takes precedence over as_text)
            only_filename: If True, only return filename and match count; if False, return detailed content
            enable_ignore: Enable .drowignore file filtering
            shell_policy: Shell policy for command parsing (auto/unix/powershell)
            as_type: Output format type for the response
            filter_empty_fields: Whether to filter empty fields in output
            filter_metadata_fields: Whether to filter metadata fields in output

        Returns:
            SearchToolResponse (or converted format based on as_type)
        """
        self._validate_initialized()
        dumping_kwargs = self._parse_dump_kwargs(locals())

        try:
            # Handle cwd
            cwd = Path(cwd or os.getcwd()).expanduser().resolve()
            if not cwd.exists():
                raise FileNotFoundError(f"Working directory does not exist: {cwd}")
            if not cwd.is_dir():
                raise ValueError(f"Working directory is not a directory: {cwd}")

            # Handle path
            search_path = Path(path).expanduser().resolve()
            if not search_path.exists():
                raise FileNotFoundError(f"Path does not exist: {search_path}")

            path_is_within_cwd = self._is_within_workspace(str(search_path), str(cwd))
            if not enable_search_outside and not path_is_within_cwd:
                raise ValueError(f"Path '{search_path}' is outside workspace '{cwd}' and external search is disabled")

            # Initialize ignore controller if needed
            controller = None
            if enable_ignore:
                controller = IgnoreController(cwd, shell=shell_policy)
                controller.load()

            def is_file_ignored(file_path_obj) -> bool:
                """Check if a file is ignored by .drowignore patterns"""
                if not controller:
                    return False
                try:
                    rel_path = os.path.relpath(str(file_path_obj), cwd)
                    return not controller.validate_access(rel_path)
                except Exception:
                    # If path processing fails, conservatively allow the file
                    return False

            # Determine files to search
            if search_path.is_file():
                # Check single file against ignore patterns
                if is_file_ignored(search_path):
                    files_to_search = []
                else:
                    files_to_search = [str(search_path)]

            elif search_path.is_dir():
                # Use Path rglob with smart exclusion patterns
                base_path = Path(search_path)
                files_to_search = []

                # Pre-process exclusion patterns for better performance
                dir_patterns = [p.rstrip('/') for p in EXT_PATTERNS_FOR_BASE_EXCLUDE if p.endswith('/')]
                file_patterns = [p.lstrip('*') for p in EXT_PATTERNS_FOR_BASE_EXCLUDE if not p.endswith('/')]

                # Use rglob with filepath_pattern, then filter efficiently
                for file_path in base_path.rglob(filepath_pattern):
                    if not file_path.is_file():
                        continue

                    # Quick directory exclusion check
                    path_parts = file_path.parts
                    if any(any(pattern in part for part in path_parts) for pattern in dir_patterns):
                        continue

                    # Quick filename exclusion check
                    if any(file_path.name.endswith(pattern) for pattern in file_patterns):
                        continue

                    # Check .drowignore patterns
                    if is_file_ignored(file_path):
                        continue

                    files_to_search.append(str(file_path))
            else:
                raise FileNotFoundError(f"Path does not exist: {search_path}")

            # Search for content pattern
            results = []
            # Compile pattern - re.error will propagate naturally for invalid regex
            try:
                pattern = re.compile(content_pattern)
            except re.error:
                # Re-raise regex errors directly (matches original behavior)
                raise

            for file_path in files_to_search:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_matches = []
                        file_total_lines = 0
                        for line_num, line in enumerate(f, 1):
                            file_total_lines = line_num
                            if pattern.search(line):
                                file_matches.append(LineMeta(
                                    line=line_num,
                                    text=line.strip(),
                                ))

                        if file_matches:
                            results.append(FileMatchMeta(
                                file=file_path,
                                matches=file_matches,
                                total_lines=file_total_lines,
                            ))
                except Exception as e:
                    self.logger.warning(f"Error reading file {file_path}: {e}")

            # Format results based on output format
            if as_graph:
                formatted_output = self._format_results_to_pretty_graph(
                    results,
                    max_matches_per_file=max_matches_per_file,
                    only_filename=only_filename,
                    as_text=as_text
                )
            elif as_text:
                formatted_output = self._format_results_to_pretty_str(
                    results,
                    max_matches_per_file=max_matches_per_file,
                    only_filename=only_filename,
                )
            else:
                formatted_output = results

            # Calculate statistics
            total_matches = sum(len(r.matches) for r in results)
            files_found = len(results)

            # Trigger callback if configured
            self._trigger_callback("search_completed", {
                "path": str(search_path),
                "content_pattern": content_pattern,
                "files_found": files_found,
                "total_matches": total_matches
            })

            self.logger.info(f"Search completed: {files_found} files found, {total_matches} total matches")

            return SearchToolResponse(
                success=True,
                content=formatted_output,
                metadata=SearchToolResponseMetadata(
                    path=path,
                    content_pattern=content_pattern,
                    filepath_pattern=file_patterns,
                    files_found=files_found,
                    total_matches=total_matches,
                )
            ).dump(**dumping_kwargs)

        except re.error as e:
            # Re-raise regex errors directly (matches original behavior)
            raise
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            self.logger.error(error_msg)

            return SearchToolResponse(
                success=False,
                error=error_msg,
                metadata=SearchToolResponseMetadata(
                    path=path,
                    content_pattern=content_pattern,
                    filepath_pattern=file_patterns,
                )
            ).dump(**dumping_kwargs)

    def _is_within_workspace(self, path: str, workspace_root: str) -> bool:
        """
        Determine whether the given path is inside the workspace directory.

        Args:
            path: The path to check. Can be relative or absolute.
            workspace_root: The absolute path to the workspace root directory.

        Returns:
            bool: True if path is inside the workspace root, False otherwise.
        """
        # Resolve both paths to their absolute canonical form
        path = Path(path).resolve()
        workspace_root = Path(workspace_root).resolve()

        try:
            # If no exception, path is within the workspace
            path.relative_to(workspace_root)
            return True
        except ValueError:
            # If ValueError is raised, path is outside workspace_root
            return False

    def _format_results_to_pretty_str(
        self,
        results: List[FileMatchMeta],
        max_matches_per_file: int = 10,
        only_filename: bool = False,
    ) -> str:
        """
        Format search results as readable text in traditional list format.

        Args:
            results: List of file search results
            max_matches_per_file: Maximum number of matches to display per file
            only_filename: If True, only show filenames without match content

        Returns:
            str: Formatted string with file paths and match content
        """
        if not results:
            return "No matching results found"

        output = f"Found {len(results)} files with matches\n\n"

        for file_result in results:
            relative_path = os.path.relpath(file_result.file)

            if (len_matches:=len(file_result.matches)) == file_result.total_lines:
                header = f"# {relative_path} (entire file content returned)\n"
            else:
                header = f"# {relative_path} ({len_matches} matches)\n"

            output += header
            if not only_filename:
                output += file_result.format_matches(max_matches_per_file=max_matches_per_file)
            output += '\n'
        return output

    def _format_results_to_pretty_graph(
        self,
        results: List[FileMatchMeta],
        max_matches_per_file: int = 10,
        only_filename: bool = False,
        as_text: bool = True,
    ):
        """
        Format search results as a tree structure for better visualization.

        Args:
            results: List of file search results
            max_matches_per_file: Maximum number of matches to display per file
            only_filename: If True, only show filenames without match content
            as_text: If True, return formatted string; if False, return tree object

        Returns:
            str or PathTreeForSearchTool:
                - If as_text=True: Formatted tree string
                - If as_text=False: PathTreeForSearchTool object
        """
        if not results:
            return "No matching results found"

        tree = TreeGraphForSearchTool.from_paths(results)

        if as_text:
            output = f"Found {len(results)} files with matches\n\n"
            output += tree.format(
                only_filename=only_filename,
                max_matches_per_file=max_matches_per_file,
            )
            return output
        return tree
