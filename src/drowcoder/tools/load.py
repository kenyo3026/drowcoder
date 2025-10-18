"""
Refactored load tool using unified tool architecture.

This module provides file loading functionality with consistent
interface and initialization pattern.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .base import BaseTool, ToolConfig, ToolResult


@dataclass
class LoadConfig(ToolConfig):
    """
    Configuration for load tool.

    Attributes:
        ensure_abs: Whether to resolve path to absolute form (default: True)
    """
    ensure_abs: bool = True


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

    def __init__(self, ensure_abs: bool = True, **kwargs):
        """
        Initialize the load tool.

        Args:
            ensure_abs: Whether to resolve path to absolute form (default: True)
            **kwargs: Additional configuration parameters (name, logger, callback, etc.)
        """
        # Set default name if not provided
        if 'name' not in kwargs:
            kwargs['name'] = 'load'

        # Add ensure_abs to config
        config_dict = kwargs.get('config', {})
        config_dict['ensure_abs'] = ensure_abs
        kwargs['config'] = config_dict

        super().__init__(**kwargs)

    def initialize(self) -> None:
        """
        Initialize the tool.

        Called automatically in __init__.
        For this simple tool, no special initialization is needed.
        """
        super().initialize()
        if self._initialized:  # Only log on first initialization
            self.logger.debug("LoadTool initialized")

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
                    "tool": "load",
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
    tool = LoadTool(ensure_abs=ensure_abs)

    # Execute and return data
    result_obj = tool.execute(file_path=file_path, ensure_abs=ensure_abs)

    # Return data (which includes error message if failed)
    return result_obj.data


# Example usage and testing
if __name__ == "__main__":
    import logging
    import tempfile

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== Testing LoadTool ===\n")

    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Hello, World!\nThis is a test file.\nLine 3")
        test_file = f.name

    try:
        # Test 1: Basic usage with class interface
        print("Test 1: Class interface - load existing file")
        tool = LoadTool(
            name="load",
            logger=logging.getLogger("test")
        )

        result = tool.execute(file_path=test_file)
        print(f"Success: {result.success}")
        print(f"File path: {result.file_path}")
        print(f"File size: {result.file_size} bytes")
        print(f"Content preview: {result.data[:50]}...")
        print(f"Metadata: {result.metadata}\n")

        # Test 2: Backward compatible function interface
        print("Test 2: Backward compatible function interface")
        content = load(test_file)
        print(f"Content: {content[:50]}...\n")

        # Test 3: Load non-existent file
        print("Test 3: Load non-existent file")
        result = tool.execute(file_path="/non/existent/file.txt")
        print(f"Success: {result.success}")
        print(f"Error: {result.error}\n")

        # Test 4: With callback
        print("Test 4: With callback")
        def my_callback(event: str, data: dict):
            print(f"  Callback triggered - Event: {event}")
            print(f"  File: {data.get('file_path')}")
            print(f"  Size: {data.get('file_size')} bytes")

        tool_with_callback = LoadTool(
            name="load",
            callback=my_callback
        )
        result = tool_with_callback.execute(file_path=test_file)
        print(f"Success: {result.success}\n")

        # Test 5: Home directory expansion
        print("Test 5: Path expansion with environment variables")
        # Create a file in temp directory
        temp_dir = tempfile.gettempdir()
        test_file2 = os.path.join(temp_dir, "test_load.txt")
        with open(test_file2, 'w') as f:
            f.write("Test content with path expansion")

        result = tool.execute(file_path=test_file2)
        print(f"Success: {result.success}")
        print(f"Resolved path: {result.file_path}\n")

        # Cleanup
        if os.path.exists(test_file2):
            os.unlink(test_file2)

        # Test 6: Error handling - calling execute before initialize
        print("Test 6: Error handling - not initialized")
        try:
            uninitialized_tool = LoadTool(auto_initialize=False)
            uninitialized_tool.execute(file_path=test_file)
        except RuntimeError as e:
            print(f"Caught expected error: {e}\n")

    finally:
        # Cleanup test file
        if os.path.exists(test_file):
            os.unlink(test_file)

    print("=== All tests completed ===")

