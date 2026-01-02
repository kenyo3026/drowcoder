import re
import logging
import pathlib
from typing import Any, Dict, List, Union, Optional, Tuple
from dataclasses import dataclass


VALID_RULE_EXTENSIONS = {'.mdc'}

logger = logging.getLogger(__name__)

@dataclass
class MDCRule:
    """Parsed MDC rule structure"""
    always_apply: bool
    description: str
    content: str
    raw: str


class MDCParser:
    """Simple parser for MDC (Markdown with YAML frontmatter) files"""

    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n(.*)$',
        re.DOTALL
    )

    @classmethod
    def parse(cls, mdc_content: str) -> MDCRule:
        """
        Parse MDC content into structured rule data.

        Args:
            mdc_content: Raw MDC file content as string

        Returns:
            MDCRule object with parsed fields
        """
        match = cls.FRONTMATTER_PATTERN.match(mdc_content.strip())

        if not match:
            # No frontmatter found, treat entire content as markdown
            return MDCRule(
                always_apply=False,
                description='',
                content=mdc_content.strip(),
                raw=mdc_content
            )

        frontmatter_raw = match.group(1)
        content = match.group(2).strip()

        # Parse frontmatter (simple YAML parsing)
        metadata = cls._parse_frontmatter(frontmatter_raw)

        return MDCRule(
            always_apply=metadata.get('alwaysApply', False),
            description=metadata.get('description', ''),
            content=content,
            raw=mdc_content
        )

    @staticmethod
    def _parse_frontmatter(frontmatter: str) -> Dict[str, Any]:
        """Simple YAML frontmatter parser. Only supports basic key: value pairs."""
        metadata = {}

        for line in frontmatter.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Convert boolean strings
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False

                metadata[key] = value

        return metadata


RULE_PROMPT_TEMPLATE = '''
<agent_requestable_workspace_rules description="These are workspace-level rules that the agent should follow. When needed, load the full contents using the provided absolute path.">
{requestable_rules}
</agent_requestable_workspace_rules>

<always_applied_workspace_rules description="These are workspace-level rules that the agent must always follow.">
{always_applied_rules}
</always_applied_workspace_rules>
'''.strip()

class RulePromptInstruction:

    rule_prompt_template = RULE_PROMPT_TEMPLATE
    no_rules_placeholder = 'No rules specified/available'

    @staticmethod
    def _load_from_directory(rules_dir: str) -> Dict[str, MDCRule]:
        """
        Load all MDC rules from a directory.

        Args:
            rules_dir: Path to directory containing .mdc files

        Returns:
            Dict of (file_path -> MDCRule)

        Raises:
            FileNotFoundError: If directory does not exist
            ValueError: If path is not a directory or contains invalid MDC files
        """
        rules_path = pathlib.Path(rules_dir).resolve()
        if not rules_path.exists():
            raise FileNotFoundError(f"directory does not exist")

        if not rules_path.is_dir():
            raise ValueError(f"not a directory")

        rules = {}

        for mdc_file in sorted(rules_path.glob('*.mdc')):
            try:
                content = mdc_file.read_text(encoding='utf-8')
                rule_content:MDCRule = MDCParser.parse(content)
                file_path = str(mdc_file.resolve())
                rules[file_path] = rule_content
            except Exception as e:
                raise ValueError(f"invalid MDC file: {str(e)}")

        return rules

    @staticmethod
    def _load(rule_path: Union[str, pathlib.Path]) -> Dict[str, MDCRule]:
        """
        Load a single rule file.

        Args:
            rule_path: Path to .mdc rule file

        Returns:
            Dict of (file_path -> MDCRule)

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If path is not a file, has invalid extension, or parse fails
        """
        rule_path = pathlib.Path(rule_path).resolve()

        if not rule_path.exists():
            raise FileNotFoundError(f"file does not exist")

        if not rule_path.is_file():
            raise ValueError(f"not a file")

        if rule_path.suffix not in VALID_RULE_EXTENSIONS:
            raise ValueError(f"invalid extension, expected {VALID_RULE_EXTENSIONS}, got {rule_path.suffix}")

        try:
            content = rule_path.read_text(encoding='utf-8')
            rule_content: MDCRule = MDCParser.parse(content)
        except Exception as e:
            raise ValueError(f"parse failed: {str(e)}")

        return {str(rule_path): rule_content}

    @classmethod
    def format(
        cls,
        rules: Optional[Union[str, pathlib.Path, List[Union[str, pathlib.Path]]]] = None,
        return_details: bool = False,
        **kwargs
    ) -> Union[str, Tuple[str, Dict[str, Optional[str]]]]:
        """
        Format rules into prompt template.

        Args:
            rules: Path(s) to rule file(s) or directory(ies) containing .mdc files.
                Can be a single path (str or pathlib.Path) or a list of paths.
            return_details: If True, return (result, details) tuple where details contains
                success/failure status for each rule.
            **kwargs: Additional template parameters

        Returns:
            If return_details=False: Formatted rules prompt string
            If return_details=True: Tuple of (formatted string, details dict)
                details dict format: {rule_path: True (success) or error_message (failure)}
        """
        if rules is None:
            if return_details:
                return '', {}
            return ''

        # Normalize to list: convert single value to list for uniform processing
        if not isinstance(rules, list):
            rules = [rules]

        rule_path_to_content = {}
        details = {}

        for rule in rules:
            rule_path = pathlib.Path(rule)

            try:
                # Handle directory or file
                if rule_path.is_dir():
                    loaded_rules = cls._load_from_directory(rule_path)
                    rule_path_to_content.update(loaded_rules)
                    # Mark all loaded rules as successful
                    for loaded_path in loaded_rules.keys():
                        details[loaded_path] = True

                elif rule_path.is_file():
                    loaded_rules = cls._load(rule_path)
                    rule_path_to_content.update(loaded_rules)
                    # Mark loaded rule as successful
                    for loaded_path in loaded_rules.keys():
                        details[loaded_path] = True

                elif rule_path.exists():
                    error_msg = f"invalid path type"
                    details[str(rule_path)] = error_msg
                else:
                    error_msg = f"path does not exist"
                    details[str(rule_path)] = error_msg
            except (FileNotFoundError, ValueError) as e:
                # Record failure in details
                details[str(rule_path)] = str(e)
                continue

        always_applied = []
        requestable = []
        for rule_path, rule_content in rule_path_to_content.items():
            if rule_content.always_apply:
                always_applied.append(rule_content.content)
            else:
                requestable.append(f'- {rule_content.description}: {rule_path}')

        params = {
            'always_applied_rules': '\n\n'.join(always_applied) if always_applied else cls.no_rules_placeholder,
            'requestable_rules': '\n'.join(requestable) if requestable else cls.no_rules_placeholder,
            **kwargs
        }

        result = cls.rule_prompt_template.format(**params)

        if return_details:
            return result, details
        return result


if __name__ == "__main__":
    # Example 1: Format rules from directory (main usage)
    print("=" * 60)
    print("Example 1: Format rules from directory")
    print("=" * 60)

    prompt = RulePromptInstruction.format(rules_dir='.cursor/rules')
    print(prompt)
    print()

    # Example 2: Format with custom rules_dir
    print("=" * 60)
    print("Example 2: Format with custom rules_dir")
    print("=" * 60)

    prompt = RulePromptInstruction.format(
        rules_dir='.cursor/rules'
    )
    print(f"✓ Successfully formatted rules!")
    print(f"✓ Output length: {len(prompt)} characters")
    print(prompt)
    print()

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)