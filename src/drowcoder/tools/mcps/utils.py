from dataclasses import dataclass
from typing import Any, Dict

import mcp


@dataclass
class OpenAICompatibleDesc:
    """
    OpenAI-compatible function description for function calling.

    Reference: https://platform.openai.com/docs/guides/function-calling#defining-functions

    Attributes:
        name: The function's name (e.g., 'get_weather')
        description: Details on when and how to use the function
        parameters: JSON schema (dict) defining the function's input arguments
        type: This should always be 'function' (default: 'function')
        strict: Whether to enforce strict mode for the function call (default: False)
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    type: str = 'function'
    strict: bool = False

    def __post_init__(self):
        """
        Validate the function description after initialization.

        Raises:
            ValueError: If type is not 'function' or if required fields are invalid
        """
        # Validate that type is always 'function'
        if self.type != 'function':
            raise ValueError(
                f"Invalid type '{self.type}'. OpenAI function descriptions "
                f"must have type='function'"
            )

    @classmethod
    def from_mcp_type_tool(cls, mcp_type_tool: mcp.types.Tool):
        # mcp_type_tool = json.loads(mcp_type_tool.model_dump_json())
        return cls(
            name = mcp_type_tool.name,
            description = mcp_type_tool.description,
            parameters = mcp_type_tool.inputSchema,
        )