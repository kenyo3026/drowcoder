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
        result: Confirmation message
        result_description: The user-provided result description
    """
    result_description: Optional[str] = None


class AttemptCompletionTool(BaseTool):
    """
    Tool for marking current task as completed.

    This is the simplest tool in the system, serving as a signal
    that the agent has completed the requested task.
    """
    name = 'attempt_completion'

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
                result=message,
                result_description=result,
                metadata={
                    "tool": self.name,
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
        return result_obj.result
    else:
        return f"Error: {result_obj.error}"

