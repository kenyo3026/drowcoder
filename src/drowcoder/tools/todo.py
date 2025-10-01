"""
Todo management system for structured task tracking in coding sessions.

This module provides a comprehensive todo system with the following features:
- Structured todo items with id, content, and status fields
- Merge and replace operations for flexible todo management
- Persistent storage with automatic checkpoint management
- Status validation and type safety
- Dynamic status type system for easy maintenance

Main functions:
- update_todos(): Create and manage todo lists with merge/replace options
- get_todos(): Load existing todos from checkpoint files
- update_todo_status(): Update individual todo status by ID

Status types: pending, in_progress, completed, cancelled
"""

import json
import pathlib
import warnings
from dataclasses import dataclass, asdict, is_dataclass
from typing import List, Union, Dict, Any, Optional

from .utils.unique_id import generate_unique_id


@dataclass(frozen=True)
class TodoStatusType:
    """Status types for todo system matching the tool specification."""
    PENDING     :str = 'pending'
    IN_PROGRESS :str = 'in_progress'
    COMPLETED   :str = 'completed'
    CANCELLED   :str = 'cancelled'

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


def validate_todo_items(todos: List[Dict[str, Any]]) -> List[TodoItem]:
    """Validate and convert todo items to TodoItem objects.

    Args:
        todos: List of todo dictionaries with id, content, and status fields

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
    existing_todos: List[TodoItem],
    new_todos: List[TodoItem]
) -> List[TodoItem]:
    """Merge new todo items with existing ones based on ID.

    Args:
        existing_todos: Current todo items
        new_todos: New todo items to merge

    Returns:
        Merged list of todo items

    Note:
        - Items with matching IDs will be updated with new values
        - Items with new IDs will be added
        - Existing items not in new_todos will be preserved

        Important: COMPLETE REPLACEMENT behavior
        - When IDs match, the entire TodoItem is replaced (not partial update)
        - ALL fields can be modified: id, content, status
        - No restrictions on which fields can be changed during merge
        - If you only want to update status, you still need to provide complete content
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


def load_existing_todos(checkpoint_path: Union[str, pathlib.Path]) -> List[TodoItem]:
    """Load existing todo items from checkpoint file.

    Args:
        checkpoint_path: Path to the todo checkpoint file

    Returns:
        List of existing TodoItem objects, empty list if file doesn't exist

    Raises:
        IOError: If file exists but cannot be read or parsed
    """
    checkpoint_path = pathlib.Path(checkpoint_path)

    if not checkpoint_path.exists():
        warnings.warn(f"Todo checkpoint file not found: {checkpoint_path}. Returning empty list.",
                     UserWarning, stacklevel=2)
        return []

    try:
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Checkpoint file must contain a list of todo items")

        existing_todos = []
        for item in data:
            if isinstance(item, dict) and all(k in item for k in ['id', 'content', 'status']):
                # Only extract the required fields to avoid unexpected keyword arguments
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
    todos: List[TodoItem],
    checkpoint_path: Union[str, pathlib.Path]
) -> None:
    """Save todo items to checkpoint file.

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


def update_todos(
    merge: bool,
    todos: List[Dict[str, Any]],
    checkpoint_path: Union[str, pathlib.Path]
) -> str:
    """Create and manage a structured task list for coding sessions.

    This is the main function that implements the update_todos tool functionality.

    Args:
        merge: Whether to merge with existing todos (True) or replace them (False)
               - merge=False: Completely replace all existing todos with new ones
               - merge=True: Merge new todos with existing ones based on ID matching
        todos: Array of todo items with id, content, and status fields
        checkpoint_path: Path to save todos. Must be provided by caller.

    Returns:
        Success message string

    Raises:
        ValueError: If todo items are invalid or missing required fields
        IOError: If checkpoint file operations fail

    Important: Merge behavior details
        - When merge=True and IDs match: COMPLETE replacement of the todo item
        - ALL fields (id, content, status) can be modified without restrictions
        - No field-level limitations - you can update any combination of fields
        - Partial updates not supported - must provide complete todo item data

    Examples:
        >>> todos = [
        ...     {"id": "task1", "content": "Implement feature A", "status": "pending"},
        ...     {"id": "task2", "content": "Write tests", "status": "in_progress"}
        ... ]
        >>> result = update_todos(merge=False, todos=todos)
        >>> print(result)
        Successfully updated TODOs. Make sure to follow and update your TODO list as you make progress. Cancel and add new TODO tasks as needed when the user makes a correction or follow-up request.
    """
    # Validate input todos
    validated_todos = validate_todo_items(todos)

    # Convert checkpoint_path to Path object
    checkpoint_path = pathlib.Path(checkpoint_path)

    # Handle merge vs replace logic
    if merge:
        # Load existing todos and merge
        # Note: merge_todo_items performs COMPLETE replacement for matching IDs
        # All fields (id, content, status) can be modified without restrictions
        existing_todos = load_existing_todos(checkpoint_path)
        final_todos = merge_todo_items(existing_todos, validated_todos)
    else:
        # Replace existing todos completely
        final_todos = validated_todos

    # Save to checkpoint
    save_todos_to_checkpoint(final_todos, checkpoint_path)

    return ("Successfully updated TODOs. Make sure to follow and update your TODO list "
            "as you make progress. Cancel and add new TODO tasks as needed when the user "
            "makes a correction or follow-up request.")


def get_todos(checkpoint_path: Union[str, pathlib.Path]) -> List[Dict[str, Any]]:
    """Load and retrieve TODO list from checkpoint file.

    Args:
        checkpoint_path: Path to the TODO checkpoint file.

    Returns:
        List of TODO dictionaries with id, content, and status fields

    Raises:
        FileNotFoundError: If the TODO file does not exist
        IOError: If failed to read or parse the TODO file
    """
    checkpoint_path = pathlib.Path(checkpoint_path)

    if not checkpoint_path.exists():
        raise FileNotFoundError(f"TODO file not found: {checkpoint_path}")

    try:
        todos = load_existing_todos(checkpoint_path)
        return [asdict(todo) for todo in todos]
    except IOError:
        raise
    except Exception as e:
        raise IOError(f"Failed to load todos from {checkpoint_path}: {e}")


# Utility functions for status management
def update_todo_status(
    todo_id: str,
    status_to: str,
    checkpoint_path: Union[str, pathlib.Path]
) -> str:
    """Update the status of a specific todo item by ID.

    Args:
        todo_id: ID of the todo item to update
        status_to: Status value for update (pending, in_progress, completed, cancelled)
        checkpoint_path: Path to checkpoint file

    Returns:
        Success message

    Raises:
        ValueError: If todo_id not found or invalid status
        IOError: If checkpoint operations fail
    """
    # Validate status
    if status_to not in TodoStatusType.values():
        raise ValueError(f"Invalid status: {status_to}")

    # Load existing todos
    existing_todos = load_existing_todos(checkpoint_path)

    # Find and update the todo
    updated = False
    for todo in existing_todos:
        if todo.id == todo_id:
            # Create new todo item with updated status
            updated_todo = TodoItem(
                id=todo.id,
                content=todo.content,
                status=status_to
            )
            # Replace in list
            index = existing_todos.index(todo)
            existing_todos[index] = updated_todo
            updated = True
            break

    if not updated:
        raise ValueError(f"Todo with ID '{todo_id}' not found")

    # Save updated todos
    save_todos_to_checkpoint(existing_todos, checkpoint_path)

    return f"Successfully updated todo '{todo_id}' status to '{status_to}'"
