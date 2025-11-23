# Todo Tool

## Overview

The `todo` tool provides a comprehensive task management system for coding sessions. It supports structured todo items with status tracking, merge and replace operations, and persistent storage with automatic checkpoint management.

## Features

- **Structured Todo Items**: Todos with id, content, and status fields
- **Status Management**: Track tasks through pending, in_progress, completed, and cancelled states
- **Merge Operations**: Update existing todos or add new ones
- **Persistent Storage**: Automatic checkpoint management with JSON storage
- **Validation**: Built-in validation for todo structure and status values

## Parameters

### Required Parameters

- **`merge`** (bool): Whether to merge with existing todos (`True`) or replace them (`False`)
- **`todos`** (List[Dict]): Array of todo items, each containing:
  - **`id`** (string): Unique identifier for the todo item
  - **`content`** (string): The description/content of the todo item
  - **`status`** (string): Current status - one of: `"pending"`, `"in_progress"`, `"completed"`, `"cancelled"`

### Optional Parameters

- **`as_type`**: Output format type (default: `PRETTY_STR`)
- **`filter_empty_fields`** (bool): Filter empty fields in output (default: True)
- **`filter_metadata_fields`** (bool): Filter metadata fields in output (default: False)

## Todo Status Types

- **`pending`**: Not yet started
- **`in_progress`**: Currently working on
- **`completed`**: Finished successfully
- **`cancelled`**: No longer needed

## Usage Examples

### Create Initial Todo List

```python
from drowcoder.tools import TodoTool

tool = TodoTool(checkpoint="./checkpoints")

response = tool.execute(
    merge=False,  # Replace any existing todos
    todos=[
        {"id": "1", "content": "Implement user authentication", "status": "in_progress"},
        {"id": "2", "content": "Add password reset feature", "status": "pending"},
        {"id": "3", "content": "Write unit tests", "status": "pending"}
    ]
)
```

### Update Todo Status (Merge)

```python
response = tool.execute(
    merge=True,  # Merge with existing todos
    todos=[
        {"id": "1", "content": "Implement user authentication", "status": "completed"},
        {"id": "2", "content": "Add password reset feature", "status": "in_progress"}
    ]
)
```

### Add New Todos (Merge)

```python
response = tool.execute(
    merge=True,
    todos=[
        {"id": "4", "content": "Update documentation", "status": "pending"},
        {"id": "5", "content": "Deploy to staging", "status": "pending"}
    ]
)
```

### Replace All Todos

```python
response = tool.execute(
    merge=False,  # Replace all existing todos
    todos=[
        {"id": "1", "content": "New task 1", "status": "pending"},
        {"id": "2", "content": "New task 2", "status": "pending"}
    ]
)
```

## Response Format

The tool returns a `TodoToolResponse` with:

- **`success`**: `True` if todos were updated successfully
- **`content`**: Success message with guidance
- **`error`**: Error message if update failed
- **`todos`**: List of `TodoItem` objects (all todos after update)
- **`metadata`**: `TodoToolResponseMetadata` containing:
  - `checkpoint_path`: Path to the checkpoint file
  - `merge`: Whether todos were merged or replaced

## Merge vs Replace Behavior

### Merge Mode (`merge=True`)

- Updates existing todos with matching IDs
- Adds new todos that don't exist
- Preserves existing todos not in the update list
- Maintains order of existing todos

### Replace Mode (`merge=False`)

- Replaces all existing todos with the new list
- Previous todos not in the new list are removed
- Use when starting a completely new task list

## Best Practices

### When to Use This Tool

Use proactively for:
1. Complex multi-step tasks (3+ distinct steps)
2. Non-trivial tasks requiring careful planning
3. User explicitly requests todo list
4. Multiple tasks provided by user
5. After receiving new instructions - capture requirements as todos
6. After completing tasks - mark complete and add follow-ups
7. When starting new tasks - mark as in_progress

### When NOT to Use

Skip for:
1. Single, straightforward tasks
2. Trivial tasks with no organizational benefit
3. Tasks completable in < 3 trivial steps
4. Purely conversational/informational requests
5. Operational actions (linting, testing, searching codebase)

### Task Management Guidelines

1. **Status Updates**: Update status in real-time as you work
2. **Mark Complete Immediately**: Mark tasks as completed right after finishing
3. **One In Progress**: Only have ONE task in_progress at a time
4. **Complete Before Starting**: Finish current tasks before starting new ones
5. **Specific Tasks**: Create specific, actionable todo items
6. **Break Down Complex Tasks**: Break complex tasks into manageable steps

## Initialization Requirements

The `TodoTool` requires a `checkpoint` path to be provided during initialization:

```python
tool = TodoTool(checkpoint="./checkpoints")
```

The checkpoint path is used to store todos in a `todos.json` file.

## Validation

The tool validates:
- Todos must be a list with at least 2 items
- Each todo must be a dictionary
- Required fields: `id`, `content`, `status`
- All fields must be strings
- Status must be one of the valid status values

## Error Handling

The tool handles various error scenarios:

- **Invalid Structure**: Returns error if todos don't meet requirements
- **Invalid Status**: Returns error if status value is invalid
- **Checkpoint Errors**: Returns error if checkpoint file operations fail
- **JSON Errors**: Returns error if checkpoint file contains invalid JSON

## Implementation Details

- **Checkpoint Storage**: Todos are stored in `{checkpoint}/todos.json`
- **JSON Format**: Todos are serialized as JSON with indentation
- **ID-Based Merging**: Merging is based on todo ID matching
- **Order Preservation**: Existing todo order is preserved during merge
- **Callback Support**: Triggers callback events on todo updates

## Related Documentation

- See [base.md](base.md) for architecture details

