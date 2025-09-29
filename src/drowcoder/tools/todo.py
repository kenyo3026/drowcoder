import json
import pathlib
from dataclasses import dataclass, asdict, is_dataclass
from typing import List, Union

from .utils.unique_id import generate_unique_id


@dataclass(frozen=True)
class ToDoStatusTypeSymbol:
    Pending    :str = ' '
    InProgress :str = '~'
    Done       :str = 'X'

@dataclass(frozen=True)
class ToDoStatusType:
    Pending    :str = 'pending'
    InProgress :str = 'in_progress'
    Done       :str = 'done'

@dataclass
class ToDoMeta:
    _id     :str
    content :str
    status  :str
    symbol  :str

@dataclass
class ToDosMeta:
    _id   :str
    title :str
    todos :List[ToDoMeta]


def parse_todo_str(todos_str: str, as_dict: bool = True) -> List[ToDoMeta]:
    """Parse TODO string into ToDoMeta objects using flexible string operations.
    
    Supports multiple TODO formats:
    - [ ] Pending task (space in brackets)
    - [] Pending task (empty brackets)
    - [~] In progress task
    - [X] Done task
    
    Args:
        todos_str: Multi-line string containing TODO items
        as_dict: If True, return list of dictionaries; if False, return ToDoMeta objects
        
    Returns:
        List of TODO items as dictionaries or ToDoMeta objects
        
    Examples:
        >>> todos_str = '''
        ... [ ] Design shopping cart structure
        ... [~] Implement add product feature
        ... [X] Implement delete product feature
        ... '''.strip()
        >>> todos = parse_todo_str(todos_str)
        >>> len(todos)
        3
        >>> todos[0]['status']
        'pending'
    
    Note:
        - Invalid lines (no bracket pattern or invalid symbols) will be ignored
        - Warnings are printed to stdout for invalid lines
        - Each TODO gets a unique 8-character ID based on content and status
    """
    todos = []
    invalid_lines = []

    for line in todos_str.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        # Find bracket pattern [X] in the line
        bracket_start = line.find('[')
        bracket_end = line.find(']', bracket_start + 1)

        if bracket_start >= 0 and bracket_end > bracket_start:
            # Extract status symbol between brackets (don't strip - space is valid!)
            symbol_char = line[bracket_start + 1:bracket_end]

            # Extract content (everything after closing bracket)
            content = line[bracket_end + 1:].strip()

            # Map symbol to status - only valid symbols
            status = None
            symbol = None

            if symbol_char == ToDoStatusTypeSymbol.Done:
                status = ToDoStatusType.Done
                symbol = ToDoStatusTypeSymbol.Done
            elif symbol_char == ToDoStatusTypeSymbol.InProgress:
                status = ToDoStatusType.InProgress
                symbol = ToDoStatusTypeSymbol.InProgress
            elif symbol_char == ToDoStatusTypeSymbol.Pending or symbol_char == '':
                status = ToDoStatusType.Pending
                symbol = ToDoStatusTypeSymbol.Pending

            if status is not None:
                _id = generate_unique_id(reference=content+status, length=8)
                todos.append(ToDoMeta(_id=_id, content=content, status=status, symbol=symbol))
            else:
                # Invalid symbol in brackets
                invalid_lines.append(line)
        else:
            # No valid bracket pattern found
            invalid_lines.append(line)

    # Show warnings if there are invalid lines
    if invalid_lines:
        print(f'Warnings: Found {len(invalid_lines)} invalid TODO lines:')
        for invalid_line in invalid_lines:
            print(f' - {invalid_line}')

    if as_dict:
        return [asdict(todo) if is_dataclass(todo) else todo for todo in todos]
    return todos

def update_todos(
    todos_str: str,
    as_dict: bool = True,
    checkpoint_path: Union[str, pathlib.Path] = None,
):
    """Create and optionally save TODO list from string.
    
    Parses a multi-line TODO string and optionally saves the result to a JSON file.
    
    Args:
        todos_str: Multi-line string containing TODO items in supported formats
        as_dict: If True, return dictionaries; if False, return ToDoMeta objects
        checkpoint_path: Optional path to save the TODO list as JSON file.
                        Parent directories will be created if they don't exist.
    
    Returns:
        List of TODO items as dictionaries or ToDoMeta objects
        
    Raises:
        IOError: If failed to write to the checkpoint file
        
    Examples:
        >>> todos_str = '''
        ... [ ] Task 1
        ... [X] Task 2
        ... '''.strip()
        >>> todos = update_todos(todos_str, checkpoint_path='todos.json')
        >>> # Creates todos.json file with the parsed TODO items
        
    Note:
        - Uses parse_todo_str() internally for parsing
        - JSON file is saved with UTF-8 encoding and pretty formatting
        - Parent directories are automatically created if needed
    """
    todos = parse_todo_str(todos_str, as_dict=as_dict)

    if checkpoint_path:
        # Ensure parent directory exists (following project pattern)
        checkpoint_path = pathlib.Path(checkpoint_path)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(todo) if is_dataclass(todo) else todo for todo in todos], f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise IOError(f"Failed to write TODO list to {checkpoint_path}: {e}")
    return todos

def get_todos(
    checkpoint_path: Union[str, pathlib.Path],
):
    """Load TODO list from JSON file.

    Args:
        checkpoint_path: Path to the TODO JSON file

    Returns:
        List of TODO dictionaries or ToDosMeta objects

    Raises:
        FileNotFoundError: If the TODO file does not exist
        IOError: If failed to read or parse the TODO file
        ValueError: If the file contains invalid JSON or TODO format
    """
    checkpoint_path = pathlib.Path(checkpoint_path)

    try:
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        raise FileNotFoundError(f"TODO file not found: {checkpoint_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in TODO file {checkpoint_path}: {e}")
    except PermissionError:
        raise IOError(f"Permission denied reading TODO file: {checkpoint_path}")
    except Exception as e:
        raise IOError(f"Failed to read TODO file {checkpoint_path}: {e}")

# def update_todo_status(
#     todos: List[dict, ToDoMeta],
#     status_to: Union[str, Type[ToDoStatusType]],
#     _id: str = None,
#     content: str = None,
# ):
#     todos = [ToDoMeta(**todo) if isinstance(todo, dict) else todo for todo in todos]

#     selected_todos = None
#     if _id or content:
#         for todo in todos:
#             if _id and _id == todo._id[:len(_id)]:
#                 selected_todo = todo
#                 break
#             elif content and content == todo.content:
#                 selected_todo = todo
#                 break

#         if selected_todos is None:
#             if _id and content:
#                 raise ValueError(f'No TODO list found with _id starting with "{_id}" or title "{title}"')
#             elif _id:
#                 raise ValueError(f'No TODO list found with _id starting with "{_id}"')
#             else:
#                 raise ValueError(f'No TODO list found with content "{content}"')

#     todos_to_update = selected_todos
