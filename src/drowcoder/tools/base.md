# Base Tool Architecture

## Overview

The `base` module provides the foundational architecture for all tools in the drowcoder system. It defines abstract base classes, common data structures, and unified interfaces that ensure consistency across all tool implementations.

## Architecture Components

### BaseTool (Abstract Base Class)

All tools inherit from `BaseTool`, which provides:

- **Unified Initialization**: Consistent configuration and setup pattern
- **Standard Interface**: Common `execute()` method signature
- **Response Handling**: Built-in support for multiple output formats
- **Logging Integration**: Automatic logger setup and management
- **Callback Support**: Event notification system for tool operations
- **Validation**: Built-in initialization state checking

### ToolResponse

Standard response format for all tool executions:

```python
@dataclass
class ToolResponse:
    tool_name: Optional[str] = None
    success: Optional[bool] = None
    content: Any = None
    error: Optional[str] = None
    metadata: Optional[ToolResponseMetadata] = None
```

**Response Fields:**
- `tool_name`: Identifier of the tool that generated the response
- `success`: Boolean indicating execution success
- `content`: The actual result data (type varies by tool)
- `error`: Error message if execution failed
- `metadata`: Additional execution metadata

**Output Formats:**
- `INTACT`: Return response object as-is
- `DICT`: Convert to dictionary
- `STR`: Convert to string representation
- `PRETTY_STR`: Convert to formatted string (default)

### ToolConfig

Base configuration for all tools:

```python
@dataclass
class ToolConfig:
    logger: Optional[logging.Logger] = None
    callback: Optional[Callable] = None
    checkpoint: Optional[Union[str, Path]] = None
```

**Configuration Options:**
- `logger`: Custom logger instance (auto-created if not provided)
- `callback`: Function to call on tool events
- `checkpoint`: Root path for tools requiring persistence

## Design Principles

### 1. Unified Interface

All tools implement the same `execute()` method signature:

```python
def execute(
    self,
    as_type: Union[str, _IntactType] = ToolResponseType.PRETTY_STR,
    filter_empty_fields: bool = True,
    filter_metadata_fields: bool = True,
    **kwargs,
) -> ToolResponse:
```

### 2. Consistent Error Handling

All tools follow the same error handling pattern:
- Return `ToolResponse` with `success=False` on errors
- Include descriptive error messages
- Log errors appropriately

### 3. Flexible Output Formatting

Tools support multiple output formats through the `as_type` parameter:
- `INTACT`: For programmatic access
- `DICT`: For structured data processing
- `STR`: For simple string output
- `PRETTY_STR`: For human-readable formatted output

### 4. Extensibility

Tools can extend base classes to add:
- Custom response metadata classes
- Tool-specific validation logic
- Specialized initialization requirements

## Usage Pattern

### Creating a New Tool

1. **Inherit from BaseTool**:
```python
class MyTool(BaseTool):
    name = 'my_tool'
```

2. **Implement execute() method**:
```python
def execute(self, **kwargs) -> Any:
    self._validate_initialized()
    dumping_kwargs = self._parse_dump_kwargs(locals())

    try:
        # Tool logic here
        return MyToolResponse(
            success=True,
            content=result,
        ).dump(**dumping_kwargs)
    except Exception as e:
        return MyToolResponse(
            success=False,
            error=str(e),
        ).dump(**dumping_kwargs)
```

3. **Define custom response classes** (optional):
```python
@dataclass
class MyToolResponse(ToolResponse):
    tool_name: str = 'my_tool'
    custom_field: Optional[str] = None
```

## Benefits

- **Consistency**: All tools behave predictably
- **Maintainability**: Common patterns reduce code duplication
- **Testability**: Unified interface simplifies testing
- **Extensibility**: Easy to add new tools following established patterns
- **Type Safety**: Dataclasses provide structure and validation

## Related Tools

All tools in the drowcoder system are built on this foundation:
- `attempt_completion`: Task completion signaling
- `execute`: Command execution
- `load`: File loading
- `search`: Content searching
- `search_and_replace`: Text replacement
- `todo`: Task management
- `write`: File writing

