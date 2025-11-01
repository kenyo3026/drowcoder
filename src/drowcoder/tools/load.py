"""
Refactored load tool using unified tool architecture.

This module provides file loading functionality with consistent
interface and initialization pattern.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .base import BaseTool, ToolResult


@dataclass
class LoadResult(ToolResult):
    """
    Result from load tool execution.

    Attributes:
        success: Whether the file loading succeeded
        data: The file content as string
        file_path: The resolved file path that was loaded
        file_size: Size of the loaded file in bytes
    """
    file_path: Optional[str] = None
    file_size: Optional[int] = None


class LoadTool(BaseTool):
    """
    Tool for loading file content as plain text.

    Supports various path formats:
    - Absolute paths: /Users/username/file.txt
    - Relative paths: ./file.txt, ../file.txt
    - Home directory: ~/file.txt
    - Environment variables: $HOME/file.txt
    """
    name = 'load'

    def execute(self, file_path: str, ensure_abs: bool = True, **kwargs) -> LoadResult:
        """
        Load the content of a file as plain text.

        This method preserves the exact functionality of the original
        load() function.

        Args:
            file_path: The path to the file to be loaded. Supports:
                      - Absolute paths: /Users/username/file.txt
                      - Relative paths: ./file.txt, ../file.txt
                      - Home directory: ~/file.txt
                      - Environment variables: $HOME/file.txt
            ensure_abs: Whether to resolve path to absolute form (default: True)
            **kwargs: Additional parameters (ignored for compatibility)

        Returns:
            LoadResult with file content or error message
        """
        self._validate_initialized()

        try:
            # Preserve original logic exactly
            if ensure_abs:
                file_path = os.path.expanduser(os.path.expandvars(file_path))

            path_obj = Path(file_path).resolve()

            # Check if file exists
            if not path_obj.exists():
                error_msg = f"Error: File '{file_path}' not found."
                self.logger.warning(error_msg)

                return LoadResult(
                    success=False,
                    data=error_msg,
                    error=error_msg,
                    file_path=str(path_obj)
                )

            # Read file content
            with open(path_obj, "r", encoding="utf-8") as f:
                content = f.read()

            # Get file size
            file_size = path_obj.stat().st_size

            # Trigger callback if configured
            self._trigger_callback("file_loaded", {
                "file_path": str(path_obj),
                "file_size": file_size,
                "content_length": len(content)
            })

            self.logger.info(f"Successfully loaded file: {path_obj} ({file_size} bytes)")

            return LoadResult(
                success=True,
                data=content,
                file_path=str(path_obj),
                file_size=file_size,
                metadata={
                    "tool": self.name,
                    "content_length": len(content),
                    "file_size_bytes": file_size
                }
            )

        except FileNotFoundError:
            error_msg = f"Error: File '{file_path}' not found."
            self.logger.error(error_msg)

            return LoadResult(
                success=False,
                data=error_msg,
                error=error_msg,
                file_path=file_path
            )

        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            self.logger.error(error_msg)

            return LoadResult(
                success=False,
                data=error_msg,
                error=error_msg,
                file_path=file_path
            )


# Backward compatible function interface
def load(file_path: str, ensure_abs: bool = True) -> str:
    """
    Load the content of a file as plain text given its file path.

    This is a backward-compatible wrapper around LoadTool.
    Preserves the exact interface and behavior of the original function.

    Args:
        file_path: The path to the file to be loaded. Supports:
                  - Absolute paths: /Users/username/file.txt
                  - Relative paths: ./file.txt, ../file.txt
                  - Home directory: ~/file.txt
                  - Environment variables: $HOME/file.txt
        ensure_abs: Whether to resolve path to absolute form (default: True)

    Returns:
        str: The content of the file as a string, or error message if failed.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    # Create tool (auto-initializes by default)
    tool = LoadTool()

    # Execute and return data
    result_obj = tool.execute(file_path=file_path, ensure_abs=ensure_abs)

    # Return data (which includes error message if failed)
    return result_obj.data

