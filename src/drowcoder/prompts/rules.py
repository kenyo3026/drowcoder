import os
import re
import platform
from typing import List, Dict, Any, Optional, NamedTuple
from dataclasses import dataclass


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
    def _load_from_directory(rules_dir: str) -> tuple[List[MDCRule], List[str]]:
        """
        Load all MDC rules from a directory.

        Args:
            rules_dir: Path to directory containing .mdc files

        Returns:
            Tuple of (list of parsed MDCRule objects, list of file paths)
        """
        import pathlib

        rules_path = pathlib.Path(rules_dir).resolve()
        if not rules_path.exists():
            return [], []

        rules = []
        file_paths = []

        for mdc_file in sorted(rules_path.glob('*.mdc')):
            try:
                content = mdc_file.read_text(encoding='utf-8')
                rule = MDCParser.parse(content)
                rules.append(rule)
                file_paths.append(str(mdc_file.resolve()))
            except Exception as e:
                # Skip files that cannot be parsed
                continue

        return rules, file_paths

    @classmethod
    def format(cls, rules_dir: Optional[str] = None, **kwargs) -> str:
        """
        Format rules into prompt template.

        Args:
            rules_dir: Path to directory containing .mdc files
            **kwargs: Additional template parameters

        Returns:
            Formatted rules prompt string
        """
        if not rules_dir:
            return ''

        rules, file_paths = cls._load_from_directory(rules_dir)

        always_applied = []
        requestable = []

        for idx, rule in enumerate(rules):
            if rule.always_apply:
                always_applied.append(rule.content)
            else:
                # For requestable rules, list description and file path
                if file_paths and idx < len(file_paths):
                    requestable.append(f'- {rule.description}: {file_paths[idx]}')
                else:
                    requestable.append(f'- {rule.description}')

        params = {
            'always_applied_rules': '\n\n'.join(always_applied) if always_applied else cls.no_rules_placeholder,
            'requestable_rules': '\n'.join(requestable) if requestable else cls.no_rules_placeholder,
            **kwargs
        }

        return cls.rule_prompt_template.format(**params)


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