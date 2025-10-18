"""
Refactored attempt_completion tool using unified tool architecture.

This module provides task completion marking functionality with consistent
interface and initialization pattern.
"""

from dataclasses import dataclass
from typing import Optional

from .base import BaseTool, ToolConfig, ToolResult


@dataclass
class AttemptCompletionConfig(ToolConfig):
    """
    Configuration for attempt_completion tool.

    Inherits all base configuration fields from ToolConfig.
    No additional fields needed for this simple tool.
    """
    pass


@dataclass
class AttemptCompletionResult(ToolResult):
    """
    Result from attempt_completion tool execution.

    Attributes:
        success: Whether the completion marking succeeded
        data: Confirmation message
        result_description: The user-provided result description
    """
    result_description: Optional[str] = None


class AttemptCompletionTool(BaseTool):
    """
    Tool for marking current task as completed.

    This is the simplest tool in the system, serving as a signal
    that the agent has completed the requested task.
    """

    def __init__(self, **kwargs):
        """
        Initialize the attempt_completion tool.

        Args:
            **kwargs: Configuration parameters (name, logger, callback, etc.)
        """
        # Set default name if not provided
        if 'name' not in kwargs:
            kwargs['name'] = 'attempt_completion'

        super().__init__(**kwargs)

    def initialize(self) -> None:
        """
        Initialize the tool.

        Called automatically in __init__.
        For this simple tool, no special initialization is needed.
        """
        super().initialize()
        if self._initialized:  # Only log on first initialization
            self.logger.debug("AttemptCompletionTool initialized (no special setup required)")

    def execute(self, result: str, **kwargs) -> AttemptCompletionResult:
        """
        Mark the current task as completed.

        This method preserves the exact functionality of the original
        attempt_completion() function.

        Args:
            result: A brief description of what was accomplished
            **kwargs: Additional parameters (ignored for compatibility)

        Returns:
            AttemptCompletionResult with success status and confirmation message
        """
        self._validate_initialized()

        try:
            # Preserve original logic exactly
            message = f"Task completed successfully: {result}"

            # Trigger callback if configured
            self._trigger_callback("task_completed", {
                "result": result,
                "message": message
            })

            self.logger.info(f"Task marked as completed: {result}")

            return AttemptCompletionResult(
                success=True,
                data=message,
                result_description=result,
                metadata={
                    "tool": "attempt_completion",
                    "result_length": len(result)
                }
            )

        except Exception as e:
            error_msg = f"Failed to mark task as completed: {str(e)}"
            self.logger.error(error_msg)

            return AttemptCompletionResult(
                success=False,
                error=error_msg,
                result_description=result
            )


# Backward compatible function interface
def attempt_completion(result: str) -> str:
    """
    Mark the current task as completed.

    This is a backward-compatible wrapper around AttemptCompletionTool.
    Preserves the exact interface and behavior of the original function.

    Args:
        result: A brief description of what was accomplished.

    Returns:
        str: Confirmation message that the task has been marked as completed.
    """
    # Create tool (auto-initializes by default)
    tool = AttemptCompletionTool()

    # Execute and return data
    result_obj = tool.execute(result=result)

    if result_obj.success:
        return result_obj.data
    else:
        return f"Error: {result_obj.error}"


# Example usage and testing
if __name__ == "__main__":
    import logging

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== Testing AttemptCompletionTool ===\n")

    # Test 1: Basic usage with class interface
    print("Test 1: Class interface")
    tool = AttemptCompletionTool(
        name="attempt_completion",
        logger=logging.getLogger("test")
    )

    result = tool.execute(result="Implemented new feature successfully")
    print(f"Success: {result.success}")
    print(f"Message: {result.data}")
    print(f"Metadata: {result.metadata}\n")

    # Test 2: Backward compatible function interface
    print("Test 2: Backward compatible function interface")
    message = attempt_completion("Fixed bug in authentication module")
    print(f"Message: {message}\n")

    # Test 3: With callback
    print("Test 3: With callback")
    def my_callback(event: str, data: dict):
        print(f"  Callback triggered - Event: {event}, Data: {data}")

    tool_with_callback = AttemptCompletionTool(
        name="attempt_completion",
        callback=my_callback
    )
    result = tool_with_callback.execute(result="Refactored codebase")
    print(f"Success: {result.success}\n")

    # Test 4: Error handling - calling execute before initialize
    print("Test 4: Error handling - not initialized")
    try:
        uninitialized_tool = AttemptCompletionTool(auto_initialize=False)
        uninitialized_tool.execute(result="This should fail")
    except RuntimeError as e:
        print(f"Caught expected error: {e}\n")

    print("=== All tests completed ===")

