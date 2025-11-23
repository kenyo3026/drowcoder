# Model Dispatcher

## Overview

The `model` module provides model configuration dispatching functionality for drowcoder agents. It organizes models by their roles (chatcompletions and postcompletions) and prepares them for use with the LiteLLM completion API.

## Features

- **Role-Based Dispatching**: Organizes models by their roles (chatcompletions, postcompletions)
- **Config Morphing**: Optional integration with ConfigMorpher for advanced configuration handling
- **Flexible Role Assignment**: Supports both simple role strings and role-task dictionaries
- **Multiple Role Support**: Models can be assigned to multiple roles simultaneously

## Model Roles

### ChatCompletions Role

Models assigned to the `chatcompletions` role are used for the main agent conversation and tool calling.

```yaml
models:
  - name: gemini
    model: gemini/gemini-2.5-flash
    roles:
      - chatcompletions
```

### PostCompletions Role

Models assigned to the `postcompletions` role are used for post-processing tasks after the main completion, such as reviewing changes or generating summaries.

```yaml
models:
  - name: gemini
    model: gemini/gemini-2.5-flash
    roles:
      - postcompletions: "review the git diff changes and checkpoint the changes to 'gitdiff.md'"
```

## Usage

### Basic Usage

```python
from drowcoder.model import ModelDispatcher

# Models configuration from YAML
models_config = [
    {
        'name': 'gemini',
        'model': 'gemini/gemini-2.5-flash',
        'temperature': 0,
        'roles': ['chatcompletions', 'postcompletions']
    }
]

# Create dispatcher
dispatcher = ModelDispatcher(models_config, morph=True)

# Access models by role
chat_models = dispatcher.for_chatcompletions
post_models = dispatcher.for_postcompletions
```

### With ConfigMorpher

```python
from config_morpher import ConfigMorpher
from drowcoder.model import ModelDispatcher
import litellm

# Load configuration
config = ConfigMorpher.from_yaml('config.yaml')
models_config = config.fetch('models')

# Create dispatcher with morphing
dispatcher = ModelDispatcher(models_config, morph=True)

# Use with LiteLLM
completion_kwargs = dispatcher.for_chatcompletions.morph(
    litellm.completion,
    start_from='models[0]'
)
```

### Role Assignment Examples

#### Simple Role String

```python
models = [
    {
        'name': 'model1',
        'model': 'gpt-4',
        'roles': ['chatcompletions']  # Simple string
    }
]
```

#### Role with Task

```python
models = [
    {
        'name': 'model1',
        'model': 'gpt-4',
        'roles': [
            'chatcompletions',
            {'postcompletions': 'Review and summarize changes'}  # Dict with task
        ]
    }
]
```

#### Multiple Roles

```python
models = [
    {
        'name': 'model1',
        'model': 'gpt-4',
        'roles': [
            'chatcompletions',
            'postcompletions'  # Same model for both roles
        ]
    }
]
```

## API Reference

### ModelRoleType

Constants for model role types.

```python
@dataclass(frozen=True)
class ModelRoleType:
    chatcompletions: str = 'chatcompletions'
    postcompletions: str = 'postcompletions'
```

**Constants**:
- `chatcompletions`: Role for main conversation and tool calling
- `postcompletions`: Role for post-processing tasks

### ModelDispatcher

Dispatcher class for organizing models by roles.

#### `__init__(models: List[dict], morph: bool = True)`

Initialize the model dispatcher.

**Parameters**:
- **`models`** (List[dict]): List of model configuration dictionaries. Each model should have:
  - `name`: Model name identifier
  - `model`: Model identifier for LiteLLM
  - `roles`: List of role assignments (strings or dicts)
  - Other model-specific configuration (temperature, api_key, etc.)
- **`morph`** (bool): If `True`, converts role groups to ConfigMorpher instances (default: `True`)

**Attributes**:
- `models`: Original models list
- `morph`: Whether morphing is enabled
- `for_chatcompletions`: Models assigned to chatcompletions role (ConfigMorpher or dict)
- `for_postcompletions`: Models assigned to postcompletions role (ConfigMorpher or dict)

#### `dispatch(morph: bool = True)`

Dispatch models to their respective role groups.

**Parameters**:
- **`morph`** (bool): If `True`, converts role groups to ConfigMorpher instances

**Process**:
1. Iterates through each model in the models list
2. For each model, checks the `roles` field
3. For each role in the roles list:
   - If role is a string: assigns model to that role
   - If role is a dict: extracts role name and task, assigns model with task
4. Creates shallow copies of models for each role assignment
5. Groups models by role into `for_chatcompletions` and `for_postcompletions`
6. Optionally converts groups to ConfigMorpher instances if `morph=True`

## Configuration Format

### YAML Configuration Example

```yaml
models:
  - name: gemini
    api_key: YOUR_API_KEY
    model: gemini/gemini-2.5-flash
    temperature: 0
    roles:
      - chatcompletions
      - postcompletions: "review the git diff changes and checkpoint the changes to 'gitdiff.md'"
```

### Model Dictionary Structure

```python
{
    'name': str,              # Model name identifier
    'model': str,             # Model identifier for LiteLLM
    'api_key': str,           # API key (optional)
    'temperature': float,     # Temperature setting (optional)
    'max_tokens': int,        # Max tokens (optional)
    'system_prompt': str,     # System prompt (optional)
    'roles': [                # List of role assignments
        str | dict            # Role string or role-task dict
    ]
}
```

## Integration with Main Module

The ModelDispatcher is used in the main execution flow:

```python
from config_morpher import ConfigMorpher
from drowcoder.model import ModelDispatcher
import litellm

# Load configuration
config_morpher = ConfigMorpher.from_yaml('config.yaml')
models_config = config_morpher.fetch('models')

# Create dispatcher
models = ModelDispatcher(models_config, morph=True)

# Prepare completion kwargs for chatcompletions
completion_kwargs = models.for_chatcompletions.morph(
    litellm.completion,
    start_from='models[0]'
)

# Prepare completion kwargs for postcompletions (if any)
if models.for_postcompletions:
    postcompletion_kwargs = models.for_postcompletions.morph(
        litellm.completion,
        start_from='models[0]'
    )

    # Get postcompletion task
    postcompletion_task = models.for_postcompletions.fetch(
        'models[0].roles.postcompletions'
    )
```

## Role Assignment Logic

### String Role Assignment

When a role is specified as a string:

```python
roles: ['chatcompletions']
```

The model is assigned to that role with no associated task.

### Dictionary Role Assignment

When a role is specified as a dictionary:

```python
roles: [{'postcompletions': 'task description'}]
```

The model is assigned to the role (key) with an associated task (value).

### Multiple Role Assignment

A model can be assigned to multiple roles:

```python
roles: [
    'chatcompletions',
    {'postcompletions': 'Review changes'}
]
```

This creates separate model instances for each role, allowing the same model configuration to be used for different purposes.

## Morphing Behavior

When `morph=True` (default), the dispatcher converts role groups to `ConfigMorpher` instances:

```python
dispatcher = ModelDispatcher(models, morph=True)

# These are ConfigMorpher instances
chat_models = dispatcher.for_chatcompletions  # ConfigMorpher
post_models = dispatcher.for_postcompletions  # ConfigMorpher

# Can use ConfigMorpher methods
completion_kwargs = chat_models.morph(litellm.completion, start_from='models[0]')
```

When `morph=False`, role groups remain as dictionaries:

```python
dispatcher = ModelDispatcher(models, morph=False)

# These are dictionaries
chat_models = dispatcher.for_chatcompletions  # dict
post_models = dispatcher.for_postcompletions  # dict
```

## Usage Examples

### Single Model, Single Role

```python
models = [
    {
        'name': 'gpt-4',
        'model': 'gpt-4',
        'roles': ['chatcompletions']
    }
]

dispatcher = ModelDispatcher(models)
# dispatcher.for_chatcompletions contains the model
# dispatcher.for_postcompletions is empty
```

### Single Model, Multiple Roles

```python
models = [
    {
        'name': 'gemini',
        'model': 'gemini/gemini-2.5-flash',
        'roles': [
            'chatcompletions',
            {'postcompletions': 'Review changes'}
        ]
    }
]

dispatcher = ModelDispatcher(models)
# Both for_chatcompletions and for_postcompletions contain model instances
```

### Multiple Models, Different Roles

```python
models = [
    {
        'name': 'gpt-4',
        'model': 'gpt-4',
        'roles': ['chatcompletions']
    },
    {
        'name': 'claude',
        'model': 'claude-3-opus',
        'roles': [{'postcompletions': 'Generate summary'}]
    }
]

dispatcher = ModelDispatcher(models)
# for_chatcompletions contains gpt-4
# for_postcompletions contains claude
```

## Best Practices

1. **Use Descriptive Names**: Use meaningful model names for easy identification
2. **Separate Roles When Needed**: Use different models for chatcompletions and postcompletions if they have different requirements
3. **Reuse Models**: The same model can be assigned to multiple roles if appropriate
4. **Enable Morphing**: Keep `morph=True` (default) for integration with ConfigMorpher and LiteLLM
5. **Document Tasks**: When using postcompletions, provide clear task descriptions

## Related Documentation

- See [checkpoint.md](checkpoint.md) for checkpoint system
- See [verbose.md](verbose.md) for verbose output system

