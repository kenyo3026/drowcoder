"""
Refactored attempt_completion tool using unified tool architecture.

This module provides task completion marking functionality with consistent
interface and initialization pattern.
"""

from dataclasses import dataclass
from typing import Union, Any

from .base import BaseTool, ToolResponse, ToolResponseMetadata, ToolResponseType, _IntactType


TOOL_NAME = 'attempt_completion'

@dataclass
class AttemptCompletionToolResponse(ToolResponse):
    """
    Response from attempt_completion tool execution.

    Extends ToolResponse with no additional fields.
    Uses standard success/content/error fields from base class.
    """
    tool_name: str = TOOL_NAME

@dataclass
class AttemptCompletionToolResponseMetadata(ToolResponseMetadata):
    """
    Metadata for attempt_completion tool response.

    Currently contains no additional fields beyond base ToolResponseMetadata.
    This class exists for consistency and future extensibility.
    """

class AttemptCompletionTool(BaseTool):
    """
    Tool for marking current task as completed.

    This is the simplest tool in the system, serving as a signal
    that the agent has completed the requested task.
    """
    name = TOOL_NAME

    def execute(
        self,
        result: str,
        as_type: Union[str, _IntactType] = ToolResponseType.PRETTY_STR,
        filter_empty_fields: bool = True,
        filter_metadata_fields: bool = True,
        **kwargs
    ) -> Any:
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
        dumping_kwargs = self._parse_dump_kwargs(locals())

        try:
            # Preserve original logic exactly
            message = f"Task completed successfully: {result}"

            # Trigger callback if configured
            self._trigger_callback("task_completed", {
                "result": result,
                "message": message
            })

            self.logger.info(f"Task marked as completed: {result}")

            return AttemptCompletionToolResponse(
                success=True,
                content=message,
            ).dump(**dumping_kwargs)

        except Exception as e:
            error_msg = f"Failed to mark task as completed: {str(e)}"
            self.logger.error(error_msg)

            return AttemptCompletionToolResponse(
                success=False,
                error=error_msg,
            ).dump(**dumping_kwargs)
