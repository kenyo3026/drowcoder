import pathlib
from typing import List

def flatten_tool_paths(tool_others: List) -> List[str]:
    """
    Flatten nested tool path structure.

    Supports:
    - Direct paths: "path/to/tool.yaml"
    - Nested structure: {"path/to/dir": ["tool1.yaml", "tool2.yaml"]}

    Args:
        tool_others: List containing paths or nested dict structures

    Returns:
        Flattened list of full tool paths
    """
    result = []
    for item in tool_others:
        if isinstance(item, str):
            # Direct path
            result.append(item)
        elif isinstance(item, dict):
            # Nested structure: {base_path: [files]}
            for base_path, files in item.items():
                if isinstance(files, list):
                    for file in files:
                        # Combine base_path with file
                        full_path = pathlib.Path(base_path) / file
                        result.append(str(full_path))
                else:
                    # Single file (not a list)
                    full_path = pathlib.Path(base_path) / files
                    result.append(str(full_path))
    return result