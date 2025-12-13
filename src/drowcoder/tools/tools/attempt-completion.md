# Attempt Completion Tool

## Overview

The `attempt_completion` tool is a special-purpose tool that signals the agent to stop iterating and mark tasks as complete. This tool is critical for controlling the agent's continuous iteration loop.

## Purpose

**[COMPLETION SIGNAL]** This tool stops the agent iteration loop and marks tasks as complete.

The drowcoder agent operates in continuous iteration mode, meaning it will continue working until explicitly told to stop. This tool provides that explicit stop signal.

## When to Use

Call this tool when:
- All user-requested tasks have been completed
- Implementation is verified and working correctly
- No remaining tasks or unresolved issues to address

**IMPORTANT:** The agent will continue iterating indefinitely until this tool is called (up to max_iterations). Simply providing a text summary is NOT sufficient to stop - you must call this tool explicitly.

## Parameters

### Required Parameters

- **`result`** (string): A brief description of what was accomplished and why the task is considered complete.

## Usage Example

```python
from drowcoder.tools import AttemptCompletionTool

tool = AttemptCompletionTool()

response = tool.execute(
    result="Successfully implemented user authentication system with login, logout, and session management features. All tests passing."
)
```

## Response Format

The tool returns a `ToolResponse` with:

- **`success`**: `True` if completion was signaled successfully
- **`content`**: Confirmation message: "Task completed successfully: {result}"
- **`error`**: `None` on success, error message on failure

## Implementation Details

- **Simplest Tool**: This is the simplest tool in the system, serving only as a completion signal
- **No Side Effects**: The tool performs no file operations or system changes
- **Callback Support**: Triggers a "task_completed" callback event if configured

## Integration

This tool is detected by the agent's `_is_task_completed()` method, which checks for the `attempt_completion` tool call to determine when to stop iteration.

The detection logic is simple and maintainable:

```python
def _is_task_completed(self, message) -> bool:
    """
    Check if the agent has marked the task as completed.

    Returns True if attempt_completion tool was called.
    """
    if not hasattr(message, 'tool_calls') or not message.tool_calls:
        return False

    return any(
        tool_call.function.name == 'attempt_completion'
        for tool_call in message.tool_calls
    )
```

## Architecture & Design Philosophy

### Design Principles

The completion mechanism is designed with several key principles:

#### 1. Complete Decoupling

- System prompt never mentions specific tool names
- Tools can be renamed without changing prompts
- New completion tools can be added seamlessly

#### 2. Self-Documenting

- Tool descriptions carry the knowledge
- LLM learns from tool descriptions, not prompt
- Easier to maintain and extend

#### 3. Standard Compliance

We use **standard OpenAI tool format** without custom metadata because:

- **Standard Compliance**: Maintains compatibility with OpenAI API specifications
- **Simplicity**: Easier to understand and maintain
- **Self-Documenting**: Tool descriptions with `[COMPLETION SIGNAL]` marker are sufficient
- **Flexibility**: Can easily extend detection logic if needed without changing tool format

### Layered Architecture

The completion mechanism follows a three-layer architecture:

```
┌─────────────────────────────────────┐
│  System Prompt Layer                │
│  - Generic completion concepts      │
│  - Iteration policy                 │
│  - Behavioral guidelines            │
│  - No specific tool names mentioned  │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│  Tool Description Layer             │
│  - Specific tool capabilities        │
│  - [COMPLETION SIGNAL] markers       │
│  - Self-documenting instructions    │
│  - Standard OpenAI format            │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│  Code Layer                         │
│  - Simple name-based detection       │
│  - Clean and maintainable           │
│  - Easy to extend if needed         │
└─────────────────────────────────────┘
```

### Extensibility

To add another completion tool (e.g., `task_done`), simply:

1. Create the tool YAML with `[COMPLETION SIGNAL]` marker
2. Update `_is_task_completed()` to check for the new tool name:

```python
# In agent.py
def _is_task_completed(self, message) -> bool:
    if not hasattr(message, 'tool_calls') or not message.tool_calls:
        return False

    completion_tools = ['attempt_completion', 'task_done']  # Add new tools here
    return any(
        tool_call.function.name in completion_tools
        for tool_call in message.tool_calls
    )
```

**Benefits of this approach**:
- ✅ No custom metadata needed (OpenAI standard format)
- ✅ System prompt remains generic
- ✅ Simple to extend when needed

### Key Design Decisions

1. **Simple Name-Based Detection**: Direct tool name check is clear and maintainable
2. **Standard Format**: Uses only OpenAI tool format (no custom metadata)
3. **Self-Contained Tool Description**: Tool description includes all necessary information
4. **Generic System Prompt**: System prompt never mentions specific tool names

## Best Practices

1. **Always Call on Completion**: Never rely on text summaries alone - always call this tool
2. **Provide Clear Results**: Include a brief but descriptive summary in the `result` parameter
3. **Verify Before Completing**: Ensure all tasks are actually complete before calling
4. **Use Appropriate Timing**: Call after verification, not before

## Related Documentation

- See [base.md](base.md) for architecture details
