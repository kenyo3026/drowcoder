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
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Union

from .base import BaseTool, ToolResponse, ToolResponseMetadata, ToolResponseType, _IntactType
from .utils.unique_id import generate_unique_id


TOOL_NAME = 'todo'

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
class TodoToolResponseMetadata(ToolResponseMetadata):
    """
    Metadata for todo tool response.

    Attributes:
        checkpoint_path: Path to the checkpoint file
        merge: Whether todos were merged or replaced
        todos_count: Number of todos in the result
    """
    checkpoint_path: Optional[str] = None
    merge: Optional[bool] = None

@dataclass
class TodoToolResponse(ToolResponse):
    """
    Response from todo tool execution.

    Extends ToolResponse with a todos field containing the list of todo items.
    """
    tool_name: str = TOOL_NAME
    todos: Optional[List[TodoItem]] = None


class TodoTool(BaseTool):
    """
    Tool for managing structured todo lists in coding sessions.

    This tool provides update operations for todos.

    Requires checkpoint_path to be provided in config for persistence.
    """
    name = TOOL_NAME

    def __init__(self, **kwargs):
        """
        Initialize TodoTool.

        Args:
            **kwargs: Configuration parameters (name, logger, callback, checkpoint_path, etc.)
                checkpoint_path is required for this tool.

        Raises:
            ValueError: If checkpoint_path is not provided
        """
        super().__init__(**kwargs)
        if self.checkpoint is None:
            raise ValueError(
                "TodoTool requires checkpoint to be provided in config. "
                "Please provide checkpoint when initializing TodoTool."
            )
        self.checkpoint_path = pathlib.Path(self.checkpoint) / 'todos.json'

    def validate_todo_items(self, todos: List[Dict[str, Any]], merge: bool = False) -> List[Dict[str, Any]]:
        """
        Validate todo items based on merge mode.

        Args:
            todos: List of todo dictionaries
            merge: Whether in merge mode (affects validation rules)

        Returns:
            List of validated todo dictionaries (not converted to TodoItem yet)

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

            # id is always required (used to identify the todo item)
            if 'id' not in todo:
                raise ValueError(
                    f"Todo item {i} missing required field: id "
                    f"(required to identify the todo item)"
                )
            if not isinstance(todo['id'], str):
                raise ValueError(f"Todo item {i} field 'id' must be a string")

            if not merge:
                # merge=False: Need complete todo information to create new todo list
                if 'content' not in todo:
                    raise ValueError(
                        f"Todo item {i} missing required field: content "
                        f"(required when merge=False to create a complete todo item)"
                    )
                if 'status' not in todo:
                    raise ValueError(
                        f"Todo item {i} missing required field: status "
                        f"(required when merge=False to create a complete todo item)"
                    )

                # Validate field types
                if not isinstance(todo['content'], str):
                    raise ValueError(f"Todo item {i} field 'content' must be a string")
                if not isinstance(todo['status'], str):
                    raise ValueError(f"Todo item {i} field 'status' must be a string")

                # Validate status value
                try:
                    TodoItem(
                        id=todo['id'],
                        content=todo['content'],
                        status=todo['status']
                    )
                except ValueError as e:
                    raise ValueError(f"Todo item {i}: {e}")
            else:
                # merge=True: Only validate provided fields
                if 'content' in todo and not isinstance(todo['content'], str):
                    raise ValueError(f"Todo item {i} field 'content' must be a string")
                if 'status' in todo and not isinstance(todo['status'], str):
                    raise ValueError(f"Todo item {i} field 'status' must be a string")

                # Validate status value if provided
                if 'status' in todo:
                    valid_statuses = TodoStatusType.values()
                    if todo['status'] not in valid_statuses:
                        raise ValueError(
                            f"Todo item {i}: Invalid status '{todo['status']}'. "
                            f"Must be one of: {valid_statuses}"
                        )

            validated_todos.append(todo)

        return validated_todos

    def merge_todo_items(
        self,
        existing_todos: List[TodoItem],
        new_todos: List[Dict[str, Any]]
    ) -> List[TodoItem]:
        """
        Merge new todo items with existing ones based on ID.

        For existing todos: Update only provided fields, keep others unchanged.
        For new todos: Require complete information (content and status).

        Args:
            existing_todos: Current todo items
            new_todos: New todo dictionaries to merge

        Returns:
            Merged list of todo items

        Raises:
            ValueError: If new todo lacks required fields
        """
        # Create a dictionary for efficient lookup
        existing_dict = {todo.id: todo for todo in existing_todos}
        existing_ids = set(existing_dict.keys())

        # Process new todos
        updated_dict = {}
        for new_todo_dict in new_todos:
            todo_id = new_todo_dict['id']
            existing_todo = existing_dict.get(todo_id)

            if existing_todo:
                # Update existing todo: fill missing fields from existing
                has_updates = False

                if 'content' in new_todo_dict:
                    content = new_todo_dict['content']
                    has_updates = True
                else:
                    content = existing_todo.content

                if 'status' in new_todo_dict:
                    status = new_todo_dict['status']
                    has_updates = True
                else:
                    status = existing_todo.status

                # Warn if nothing is actually updated
                if not has_updates:
                    self.logger.warning(
                        f"Todo with id='{todo_id}' has no fields to update "
                        f"(only id provided, no actual changes made)"
                    )
            else:
                # New todo: require complete information
                missing_fields = [
                    field for field in ['content', 'status']
                    if field not in new_todo_dict
                ]
                if missing_fields:
                    raise ValueError(
                        f"New todo with id='{todo_id}' requires both content and status fields. "
                        f"Missing: {', '.join(missing_fields)}"
                    )
                content = new_todo_dict['content']
                status = new_todo_dict['status']

            # Create TodoItem (this will validate status)
            updated_dict[todo_id] = TodoItem(
                id=todo_id,
                content=content,
                status=status
            )

        # Build result: preserve order of existing todos, then add new ones
        result = []

        # First, add existing items in their original order (updated if in new_todos)
        for todo in existing_todos:
            if todo.id in updated_dict:
                result.append(updated_dict[todo.id])
            else:
                result.append(todo)

        # Then add completely new items
        for new_todo_dict in new_todos:
            if new_todo_dict['id'] not in existing_ids:
                result.append(updated_dict[new_todo_dict['id']])

        return result

    def save_todos_to_checkpoint(
        self,
        todos: List[TodoItem]
    ) -> None:
        """
        Save todo items to checkpoint file.

        Args:
            todos: List of TodoItem objects to save

        Raises:
            IOError: If failed to write to checkpoint file
        """
        checkpoint_path = pathlib.Path(self.checkpoint_path)
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
        as_type: Union[str, _IntactType] = ToolResponseType.PRETTY_STR,
        filter_empty_fields: bool = True,
        filter_metadata_fields: bool = False,
        **kwargs
    ) -> Any:
        """
        Main execution interface for agent - delegates to update_todos.

        This is the primary interface exposed to the agent, which internally
        calls update_todos() to perform the actual work.

        Args:
            merge: Whether to merge with existing todos or replace them
            todos: Array of todo items with id, content, and status fields
            as_type: Output format type for the response
            filter_empty_fields: Whether to filter empty fields in output
            filter_metadata_fields: Whether to filter metadata fields in output
            **kwargs: Additional parameters (ignored for compatibility)

        Returns:
            TodoToolResponse (or converted format based on as_type)
        """
        return self.update_todos(
            merge=merge,
            todos=todos,
            as_type=as_type,
            filter_empty_fields=filter_empty_fields,
            filter_metadata_fields=filter_metadata_fields
        )

    def update_todos(
        self,
        merge: bool,
        todos: List[Dict[str, Any]],
        as_type: Union[str, _IntactType] = ToolResponseType.PRETTY_STR,
        filter_empty_fields: bool = True,
        filter_metadata_fields: bool = True,
    ) -> Any:
        """
        Create and manage a structured task list for coding sessions.

        Args:
            merge: Whether to merge with existing todos (True) or replace them (False)
                   - False: Replace all todos (requires id, content, status for each item)
                   - True: Update existing todos (requires id, optional content/status)
            todos: Array of todo items
                   - merge=False: All items need id, content, status
                   - merge=True: Existing items only need id + fields to update
                                 New items need id, content, status
            as_type: Output format type for the response
            filter_empty_fields: Whether to filter empty fields in output
            filter_metadata_fields: Whether to filter metadata fields in output

        Returns:
            TodoToolResponse (or converted format based on as_type)

        Raises:
            ValueError: If todo items are invalid
            IOError: If checkpoint file operations fail
        """
        self._validate_initialized()
        dumping_kwargs = self._parse_dump_kwargs(locals())

        # Convert checkpoint_path to Path object
        checkpoint_path = pathlib.Path(self.checkpoint_path)

        try:
            # Validate input todos based on merge mode
            validated_todos = self.validate_todo_items(todos, merge=merge)

            # Handle merge vs replace logic
            if merge:
                # Load existing todos from checkpoint file
                existing_todos = []
                if checkpoint_path.exists():
                    try:
                        with open(checkpoint_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        if not isinstance(data, list):
                            raise ValueError("Checkpoint file must contain a list of todo items")

                        for item in data:
                            if isinstance(item, dict) and all(k in item for k in ['id', 'content', 'status']):
                                existing_todos.append(TodoItem(
                                    id=item['id'],
                                    content=item['content'],
                                    status=item['status']
                                ))
                    except json.JSONDecodeError as e:
                        raise IOError(f"Invalid JSON in checkpoint file {checkpoint_path}: {e}")
                    except Exception as e:
                        raise IOError(f"Failed to load checkpoint file {checkpoint_path}: {e}")

                # Merge: validated_todos are dicts, merge_todo_items will create TodoItems
                final_todos = self.merge_todo_items(existing_todos, validated_todos)
            else:
                # Replace: Convert validated dicts to TodoItems
                final_todos = [
                    TodoItem(
                        id=todo['id'],
                        content=todo['content'],
                        status=todo['status']
                    )
                    for todo in validated_todos
                ]

            # Save to checkpoint
            self.save_todos_to_checkpoint(final_todos)

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

            return TodoToolResponse(
                success=True,
                content=message,
                todos=final_todos,
                metadata=TodoToolResponseMetadata(
                    checkpoint_path=str(checkpoint_path)
                )
            ).dump(**dumping_kwargs)

        except (ValueError, TypeError) as e:
            self.logger.error(f"Todo validation error: {e}")
            return TodoToolResponse(
                success=False,
                error=str(e),
                metadata=TodoToolResponseMetadata(
                    checkpoint_path=str(checkpoint_path)
                )
            ).dump(**dumping_kwargs)
        except IOError as e:
            self.logger.error(f"Todo checkpoint error: {e}")
            return TodoToolResponse(
                success=False,
                error=str(e),
                metadata=TodoToolResponseMetadata(
                    checkpoint_path=str(checkpoint_path)
                )
            ).dump(**dumping_kwargs)
