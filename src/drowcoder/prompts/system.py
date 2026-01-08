import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union, Tuple

from .rules import RulePromptInstruction
from .instructions import InstructionFactory, InstructionType


@dataclass
class SystemPromptFormatDetails:
    rules: Dict = field(default_factory=dict)

class SystemPromptInstruction:

    @staticmethod
    def _format_tool(tool_schema: Union[str, Dict[str, Any]]) -> str:

        if isinstance(tool_schema, str):
            tool_schema = json.loads(tool_schema)
            tool_schema = json.dumps(tool_schema, indent=4, ensure_ascii=False)
        elif isinstance(tool_schema, dict):
            tool_schema = json.dumps(tool_schema, indent=4, ensure_ascii=False)
        else:
            raise TypeError(f"tool_schema must be dict or str, got {type(tool_schema).__name__}")

        return f'<tool>\n{tool_schema}\n</tool>'

    @staticmethod
    def _get_default_env() -> Dict[str, str]:
        import platform
        return {
            'os_name': platform.system(),
            'workspace_path': os.getcwd(),
            'shell_path': os.environ.get('SHELL', 'UNKNOWN'),
            **platform.uname()._asdict(),
        }

    @classmethod
    def format(
        cls,
        tools: Optional[List[str]] = None,
        rules: Optional[str] = None,
        instruction: Optional[Union[str, InstructionType]] = None,
        return_details: bool = False,
        **kwargs
    ) -> Union[str, Tuple[str, 'SystemPromptFormatDetails']]:
        """
        Format system prompt template.

        Args:
            tools: List of tool schemas or formatted tool string
            rules: Path(s) to rule file(s) or directory(ies)
            instruction: Optional instruction type to use. Can be:
                - None: Uses InstructionFactory.EMPTY (empty instruction)
                - str: Instruction type name (e.g., 'CODER', 'coder' - will be converted to uppercase)
                - InstructionType: InstructionType constant (e.g., InstructionType.CODER)
            return_details: If True, return (result, details) tuple where details contains
                success/failure status for each rule.
            **kwargs: Additional template parameters

        Returns:
            If return_details=False: Formatted system prompt string
            If return_details=True: Tuple of (formatted string, SystemPromptFormatDetails)
                SystemPromptFormatDetails.rules format: {rule_path: True (success) or error_message (failure)}
        """
        params = {**cls._get_default_env(), **kwargs}

        if not tools:
            params['tools'] = ''
        elif isinstance(tools, list):
            params['tools'] = '\n'.join([cls._format_tool(tool) for tool in tools])
        else:
            params['tools'] = tools

        # Load and format rules if rules_dir is provided
        format_details = SystemPromptFormatDetails()
        if rules:
            if return_details:
                params['rules'], format_details.rules = RulePromptInstruction.format(rules=rules, return_details=True)
            else:
                params['rules'] = RulePromptInstruction.format(rules=rules, return_details=False)
        else:
            params['rules'] = RulePromptInstruction.no_rules_placeholder

        try:
            if instruction is None:
                instruction_template = InstructionFactory.EMPTY
            else:
                if isinstance(instruction, str):
                    instruction = instruction.upper()
                instruction_template = getattr(InstructionFactory, instruction, InstructionFactory.EMPTY)
            result = instruction_template.format(**params)

            if return_details:
                return result, format_details
            return result

        except Exception as e:
            raise RuntimeError(f"Failed to format system prompt: {str(e)}")


if __name__ == "__main__":

    prompt = SystemPromptInstruction.format(
        tools=['tool1_schema', 'tool2_schema']
    )

    prompt = SystemPromptInstruction.format(
        tools=['tool1_schema'],
        os_name='Linux',
        workspace_path='/home/user'
    )

    json_tools = [
        {"name": "search", "description": "Search tool"},
        {"name": "edit", "description": "Edit tool"}
    ]
    prompt = SystemPromptInstruction.format(
        tools=json_tools,
        os_name='Linux',
        workspace_path='/home/user'
    )