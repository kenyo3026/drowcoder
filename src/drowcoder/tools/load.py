"""
Refactored load tool using unified tool architecture.

This module provides file loading functionality with consistent
interface and initialization pattern.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from .base import BaseTool, ToolResponse, ToolResponseMetadata, ToolResponseType, _IntactType


TOOL_NAME = 'load'

@dataclass
class LoadToolResponse(ToolResponse):
    """
    Response from load tool execution.

    Extends ToolResponse for file loading operations.
    The content field contains the loaded file content as a string.
    """
    tool_name: str = TOOL_NAME

@dataclass
class LoadToolResponseMetadata(ToolResponseMetadata):
    """
    Response metadata from load tool execution.

    Extends ToolResponseMetadata with load-specific fields.

    Attributes:
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
    name = TOOL_NAME

    def execute(
        self,
        file_path: str,
        ensure_abs: bool = True,
        as_type: Union[str, _IntactType] = ToolResponseType.PRETTY_STR,
        filter_empty_fields: bool = True,
        filter_metadata_fields: bool = False,
        **kwargs,
    ) -> Any:
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
            as_type: Output format type for the response
            filter_empty_fields: Whether to filter empty fields in output
            filter_metadata_fields: Whether to filter metadata fields in output
            **kwargs: Additional parameters (ignored for compatibility)

        Returns:
            LoadToolResponse (or converted format based on as_type)
        """
        self._validate_initialized()
        dumping_kwargs = self._parse_dump_kwargs(locals())

        try:
            # Preserve original logic exactly
            if ensure_abs:
                file_path = os.path.expanduser(os.path.expandvars(file_path))

            path_obj = Path(file_path).resolve()

            # Check if file exists
            if not path_obj.exists():
                error_msg = f"Error: File '{file_path}' not found."
                self.logger.warning(error_msg)

                return LoadToolResponse(
                    success=False,
                    error=error_msg,
                    metadata=LoadToolResponseMetadata(
                        file_path = str(path_obj)
                    ),
                ).dump(**dumping_kwargs)

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

            return LoadToolResponse(
                success=True,
                content=content,
                metadata=LoadToolResponseMetadata(
                    file_path=str(path_obj),
                    file_size=file_size
                )
            ).dump(**dumping_kwargs)

        except FileNotFoundError:
            error_msg = f"Error: File '{file_path}' not found."
            self.logger.error(error_msg)

            return LoadToolResponse(
                success=False,
                error=error_msg
            ).dump(**dumping_kwargs)

        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            self.logger.error(error_msg)

            return LoadToolResponse(
                success=False,
                error=error_msg,
                metadata=LoadToolResponseMetadata(
                    file_path=file_path
                )
            ).dump(**dumping_kwargs)
