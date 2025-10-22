"""
Refactored todo management tool using unified tool architecture.

This module provides a comprehensive todo system with:
- Structured todo items with id, content, and status fields
- Merge and replace operations for flexible todo management
- Persistent storage with automatic checkpoint management
- Unified tool interface with BaseTool
"""

import json
import pathlib
import warnings
from dataclasses import dataclass, asdict
from typing import List, Union, Dict, Any, Optional

from .base import BaseTool, ToolConfig, ToolResult
from .utils.unique_id import generate_unique_id


@dataclass(frozen=True)
class TodoStatusType:
    """Status types for todo system matching the tool specification."""
    PENDING: str = 'pending'
    IN_PROGRESS: str = 'in_progress'
    COMPLETED: str = 'completed'
    CANCELLED: str = 'cancelled'

    @classmethod
    def values(cls):
        """Return all valid status values dynamically using annotations."""
        return [getattr(cls, attr) for attr in cls.__annotations__.keys()]


@dataclass
class TodoItem:
    """Data structure for individual todo items."""
    id: str
    content: str
    status: str

    def __post_init__(self):
        """Validate status values."""
        valid_statuses = TodoStatusType.values()
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status '{self.status}'. Must be one of: {valid_statuses}")


@dataclass
class TodoConfig(ToolConfig):
    """
    Configuration for todo tool.

    Attributes:
        checkpoint_path: Path to save/load todos
    """
    checkpoint_path: Optional[Union[str, pathlib.Path]] = None


@dataclass
class TodoResult(ToolResult):
    """
    Result from todo tool execution.

    Attributes:
        todos: List of todo items (for get_todos operation)
    """
    todos: Optional[List[Dict[str, Any]]] = None


class TodoTool(BaseTool):
    """
    Tool for managing structured todo lists in coding sessions.

    This tool provides update, get, and status update operations for todos.
    """

    def __init__(self, checkpoint_path: Optional[Union[str, pathlib.Path]] = None, **kwargs):
        """
        Initialize TodoTool with optional checkpoint path.

        Args:
            checkpoint_path: Optional default checkpoint path
            **kwargs: Additional configuration parameters
        """
        if 'name' not in kwargs:
            kwargs['name'] = 'todo'

        # Initialize with base class
        super().__init__(**kwargs)

        # Store checkpoint_path as instance attribute
        self.checkpoint_path = checkpoint_path

    def initialize(self) -> None:
        """Initialize the todo tool."""
        super().initialize()
        if self._initialized:
            self.logger.debug("TodoTool initialized")

    def validate_todo_items(self, todos: List[Dict[str, Any]]) -> List[TodoItem]:
        """
        Validate and convert todo items to TodoItem objects.

        Args:
            todos: List of todo dictionaries

        Returns:
            List of validated TodoItem objects

        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If todos is not a list or items are not dictionaries
        """
        if not isinstance(todos, list):
            raise TypeError("todos must be a list")

        if len(todos) < 2:
            raise ValueError("At least 2 todo items are required")

        validated_todos = []

        for i, todo in enumerate(todos):
            if not isinstance(todo, dict):
                raise TypeError(f"Todo item {i} must be a dictionary")

            # Check required fields
            required_fields = ['id', 'content', 'status']
            for field in required_fields:
                if field not in todo:
                    raise ValueError(f"Todo item {i} missing required field: {field}")
                if not isinstance(todo[field], str):
                    raise ValueError(f"Todo item {i} field '{field}' must be a string")

            # Create and validate TodoItem
            try:
                todo_item = TodoItem(
                    id=todo['id'],
                    content=todo['content'],
                    status=todo['status']
                )
                validated_todos.append(todo_item)
            except ValueError as e:
                raise ValueError(f"Todo item {i}: {e}")

        return validated_todos

    def merge_todo_items(
        self,
        existing_todos: List[TodoItem],
        new_todos: List[TodoItem]
    ) -> List[TodoItem]:
        """
        Merge new todo items with existing ones based on ID.

        Args:
            existing_todos: Current todo items
            new_todos: New todo items to merge

        Returns:
            Merged list of todo items
        """
        # Create a dictionary for efficient lookup
        existing_dict = {todo.id: todo for todo in existing_todos}

        # Update or add new items
        for new_todo in new_todos:
            existing_dict[new_todo.id] = new_todo

        # Return as list, preserving order where possible
        result = []

        # First, add existing items in their original order (updated if needed)
        existing_ids = {todo.id for todo in existing_todos}
        for todo in existing_todos:
            if todo.id in existing_dict:
                result.append(existing_dict[todo.id])

        # Then add completely new items
        for new_todo in new_todos:
            if new_todo.id not in existing_ids:
                result.append(new_todo)

        return result

    def load_existing_todos(self, checkpoint_path: Union[str, pathlib.Path]) -> List[TodoItem]:
        """
        Load existing todo items from checkpoint file.

        Args:
            checkpoint_path: Path to the todo checkpoint file

        Returns:
            List of existing TodoItem objects, empty list if file doesn't exist

        Raises:
            IOError: If file exists but cannot be read or parsed
        """
        checkpoint_path = pathlib.Path(checkpoint_path)

        if not checkpoint_path.exists():
            warnings.warn(
                f"Todo checkpoint file not found: {checkpoint_path}. Returning empty list.",
                UserWarning,
                stacklevel=2
            )
            return []

        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("Checkpoint file must contain a list of todo items")

            existing_todos = []
            for item in data:
                if isinstance(item, dict) and all(k in item for k in ['id', 'content', 'status']):
                    filtered_item = {
                        'id': item['id'],
                        'content': item['content'],
                        'status': item['status']
                    }
                    existing_todos.append(TodoItem(**filtered_item))

            return existing_todos

        except json.JSONDecodeError as e:
            raise IOError(f"Invalid JSON in checkpoint file {checkpoint_path}: {e}")
        except Exception as e:
            raise IOError(f"Failed to load checkpoint file {checkpoint_path}: {e}")

    def save_todos_to_checkpoint(
        self,
        todos: List[TodoItem],
        checkpoint_path: Union[str, pathlib.Path]
    ) -> None:
        """
        Save todo items to checkpoint file.

        Args:
            todos: List of TodoItem objects to save
            checkpoint_path: Path to save the checkpoint file

        Raises:
            IOError: If failed to write to checkpoint file
        """
        checkpoint_path = pathlib.Path(checkpoint_path)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Convert to dictionaries for JSON serialization
            todos_data = [asdict(todo) for todo in todos]

            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(todos_data, f, indent=4, ensure_ascii=False)

        except Exception as e:
            raise IOError(f"Failed to write todos to {checkpoint_path}: {e}")

    def execute(
        self,
        merge: bool,
        todos: List[Dict[str, Any]],
        checkpoint_path: Optional[Union[str, pathlib.Path]] = None,
        **kwargs
    ) -> TodoResult:
        """
        Main execution interface for agent - delegates to update_todos.

        This is the primary interface exposed to the agent, which internally
        calls update_todos() to perform the actual work.

        Args:
            merge: Whether to merge with existing todos or replace them
            todos: Array of todo items with id, content, and status fields
            checkpoint_path: Path to save todos
            **kwargs: Additional parameters

        Returns:
            TodoResult from update_todos operation
        """
        return self.update_todos(merge=merge, todos=todos, checkpoint_path=checkpoint_path, **kwargs)

    def update_todos(
        self,
        merge: bool,
        todos: List[Dict[str, Any]],
        checkpoint_path: Optional[Union[str, pathlib.Path]] = None,
        **kwargs
    ) -> TodoResult:
        """
        Create and manage a structured task list for coding sessions.

        Args:
            merge: Whether to merge with existing todos (True) or replace them (False)
            todos: Array of todo items with id, content, and status fields
            checkpoint_path: Path to save todos (uses config default if not provided)
            **kwargs: Additional parameters (ignored for compatibility)

        Returns:
            TodoResult with success status and message

        Raises:
            ValueError: If todo items are invalid or checkpoint_path not provided
            IOError: If checkpoint file operations fail
        """
        self._validate_initialized()

        # Get checkpoint path
        if checkpoint_path is None:
            checkpoint_path = self.checkpoint_path
        if checkpoint_path is None:
            raise ValueError("checkpoint_path must be provided either in config or as parameter")

        try:
            # Validate input todos
            validated_todos = self.validate_todo_items(todos)

            # Convert checkpoint_path to Path object
            checkpoint_path = pathlib.Path(checkpoint_path)

            # Handle merge vs replace logic
            if merge:
                existing_todos = self.load_existing_todos(checkpoint_path)
                final_todos = self.merge_todo_items(existing_todos, validated_todos)
            else:
                final_todos = validated_todos

            # Save to checkpoint
            self.save_todos_to_checkpoint(final_todos, checkpoint_path)

            message = ("Successfully updated TODOs. Make sure to follow and update your TODO list "
                      "as you make progress. Cancel and add new TODO tasks as needed when the user "
                      "makes a correction or follow-up request.")

            # Trigger callback if configured
            if self.callback:
                self.callback({
                    'event': 'todos_updated',
                    'merge': merge,
                    'count': len(final_todos),
                    'checkpoint_path': str(checkpoint_path)
                })

            return TodoResult(
                success=True,
                data=message,
                metadata={
                    'merge': merge,
                    'todos_count': len(final_todos),
                    'checkpoint_path': str(checkpoint_path)
                }
            )

        except (ValueError, TypeError) as e:
            self.logger.error(f"Todo validation error: {e}")
            return TodoResult(
                success=False,
                error=str(e),
                metadata={'operation': 'update_todos'}
            )
        except IOError as e:
            self.logger.error(f"Todo checkpoint error: {e}")
            return TodoResult(
                success=False,
                error=str(e),
                metadata={'operation': 'update_todos'}
            )

    def get_todos(self, checkpoint_path: Optional[Union[str, pathlib.Path]] = None) -> TodoResult:
        """
        Load and retrieve TODO list from checkpoint file.

        Args:
            checkpoint_path: Path to the TODO checkpoint file

        Returns:
            TodoResult with list of TODO dictionaries

        Raises:
            ValueError: If checkpoint_path not provided
        """
        self._validate_initialized()

        # Get checkpoint path
        if checkpoint_path is None:
            checkpoint_path = self.checkpoint_path
        if checkpoint_path is None:
            raise ValueError("checkpoint_path must be provided either in config or as parameter")

        checkpoint_path = pathlib.Path(checkpoint_path)

        if not checkpoint_path.exists():
            return TodoResult(
                success=False,
                error=f"TODO file not found: {checkpoint_path}",
                metadata={'operation': 'get_todos'}
            )

        try:
            todos = self.load_existing_todos(checkpoint_path)
            todos_data = [asdict(todo) for todo in todos]

            return TodoResult(
                success=True,
                data=todos_data,
                todos=todos_data,
                metadata={
                    'todos_count': len(todos_data),
                    'checkpoint_path': str(checkpoint_path)
                }
            )
        except IOError as e:
            self.logger.error(f"Failed to load todos: {e}")
            return TodoResult(
                success=False,
                error=str(e),
                metadata={'operation': 'get_todos'}
            )

    def update_todo_status(
        self,
        todo_id: str,
        status_to: str,
        checkpoint_path: Optional[Union[str, pathlib.Path]] = None
    ) -> TodoResult:
        """
        Update the status of a specific todo item by ID.

        Args:
            todo_id: ID of the todo item to update
            status_to: Status value for update
            checkpoint_path: Path to checkpoint file

        Returns:
            TodoResult with success status and message
        """
        self._validate_initialized()

        # Get checkpoint path
        if checkpoint_path is None:
            checkpoint_path = self.checkpoint_path
        if checkpoint_path is None:
            raise ValueError("checkpoint_path must be provided either in config or as parameter")

        # Validate status
        if status_to not in TodoStatusType.values():
            return TodoResult(
                success=False,
                error=f"Invalid status: {status_to}",
                metadata={'operation': 'update_todo_status'}
            )

        try:
            # Load existing todos
            existing_todos = self.load_existing_todos(checkpoint_path)

            # Find and update the todo
            updated = False
            for i, todo in enumerate(existing_todos):
                if todo.id == todo_id:
                    updated_todo = TodoItem(
                        id=todo.id,
                        content=todo.content,
                        status=status_to
                    )
                    existing_todos[i] = updated_todo
                    updated = True
                    break

            if not updated:
                return TodoResult(
                    success=False,
                    error=f"Todo with ID '{todo_id}' not found",
                    metadata={'operation': 'update_todo_status'}
                )

            # Save updated todos
            self.save_todos_to_checkpoint(existing_todos, checkpoint_path)

            message = f"Successfully updated todo '{todo_id}' status to '{status_to}'"

            return TodoResult(
                success=True,
                data=message,
                metadata={
                    'todo_id': todo_id,
                    'status': status_to,
                    'checkpoint_path': str(checkpoint_path)
                }
            )

        except IOError as e:
            self.logger.error(f"Failed to update todo status: {e}")
            return TodoResult(
                success=False,
                error=str(e),
                metadata={'operation': 'update_todo_status'}
            )


# Backward-compatible function interfaces
def update_todos(
    merge: bool,
    todos: List[Dict[str, Any]],
    checkpoint_path: Union[str, pathlib.Path]
) -> str:
    """
    Create and manage a structured task list for coding sessions.

    This is the backward-compatible function interface that wraps TodoTool.

    Args:
        merge: Whether to merge with existing todos or replace them
        todos: Array of todo items with id, content, and status fields
        checkpoint_path: Path to save todos

    Returns:
        Success message string

    Raises:
        ValueError: If todo items are invalid
        IOError: If checkpoint file operations fail
    """
    tool = TodoTool(checkpoint_path=checkpoint_path)
    result = tool.execute(merge=merge, todos=todos, checkpoint_path=checkpoint_path)

    if not result.success:
        if isinstance(result.error, str) and 'Invalid' in result.error:
            raise ValueError(result.error)
        else:
            raise IOError(result.error)

    return result.data


def get_todos(checkpoint_path: Union[str, pathlib.Path]) -> List[Dict[str, Any]]:
    """
    Load and retrieve TODO list from checkpoint file.

    This is the backward-compatible function interface.

    Args:
        checkpoint_path: Path to the TODO checkpoint file

    Returns:
        List of TODO dictionaries

    Raises:
        FileNotFoundError: If the TODO file does not exist
        IOError: If failed to read or parse the TODO file
    """
    tool = TodoTool(checkpoint_path=checkpoint_path)
    result = tool.get_todos(checkpoint_path=checkpoint_path)

    if not result.success:
        if 'not found' in result.error.lower():
            raise FileNotFoundError(result.error)
        else:
            raise IOError(result.error)

    return result.data


def update_todo_status(
    todo_id: str,
    status_to: str,
    checkpoint_path: Union[str, pathlib.Path]
) -> str:
    """
    Update the status of a specific todo item by ID.

    This is the backward-compatible function interface.

    Args:
        todo_id: ID of the todo item to update
        status_to: Status value for update
        checkpoint_path: Path to checkpoint file

    Returns:
        Success message

    Raises:
        ValueError: If todo_id not found or invalid status
        IOError: If checkpoint operations fail
    """
    tool = TodoTool(checkpoint_path=checkpoint_path)
    result = tool.update_todo_status(todo_id=todo_id, status_to=status_to, checkpoint_path=checkpoint_path)

    if not result.success:
        if 'Invalid status' in result.error or 'not found' in result.error:
            raise ValueError(result.error)
        else:
            raise IOError(result.error)

    return result.data


