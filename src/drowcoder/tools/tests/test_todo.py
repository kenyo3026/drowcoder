"""
Unit tests for todo tool.

Tests cover:
- Basic todo operations (create, read, update)
- Merge vs replace operations
- Status validation and updates
- Edge cases (empty todos, invalid status, duplicate IDs)
- Unicode and special characters
- File I/O operations
- TodoTool class interface
- Performance benchmarks

Usage:
    # Test original todo tool
    python -m src.drowcoder.tools.tests.test_todo --module todo

    # Test refactored todo tool
    python -m src.drowcoder.tools.tests.test_todo --module todo_refactor
"""

import pytest
import sys
import os
import tempfile
import json
import time
from pathlib import Path
import importlib

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Get module name from environment variable or use default
TEST_MODULE = os.environ.get('TEST_TODO_MODULE', 'todo')

# Dynamically import the specified module
todo_module = importlib.import_module(f'drowcoder.tools.{TEST_MODULE}')
update_todos = todo_module.update_todos
get_todos = todo_module.get_todos
update_todo_status = todo_module.update_todo_status
TodoTool = getattr(todo_module, 'TodoTool', None)
TodoResult = getattr(todo_module, 'TodoResult', None)
TodoItem = todo_module.TodoItem
TodoStatusType = todo_module.TodoStatusType


@pytest.fixture
def tmp_checkpoint(tmp_path):
    """Create temporary checkpoint file path."""
    checkpoint_path = tmp_path / "todos.json"
    yield checkpoint_path
    # Cleanup handled by tmp_path fixture


class TestTodoBasic:
    """Basic todo functionality tests."""

    def test_create_simple_todo(self, tmp_checkpoint):
        """Test creating a simple todo list."""
        todos = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'in_progress'}
        ]

        result = update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)
        assert "Successfully" in result or "saved" in result.lower()

        # Verify file was created
        assert tmp_checkpoint.exists()

        # Verify content
        loaded_todos = get_todos(tmp_checkpoint)
        assert len(loaded_todos) == 2
        assert loaded_todos[0]['id'] == 'task1'
        assert loaded_todos[1]['id'] == 'task2'

    def test_create_minimum_todos(self, tmp_checkpoint):
        """Test creating minimum required todos (at least 2)."""
        todos = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'pending'}
        ]

        result = update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)
        assert "Successfully" in result or "saved" in result.lower()

        loaded_todos = get_todos(tmp_checkpoint)
        assert len(loaded_todos) == 2

    def test_all_status_types(self, tmp_checkpoint):
        """Test all valid status types."""
        todos = [
            {'id': 'task1', 'content': 'Pending task', 'status': 'pending'},
            {'id': 'task2', 'content': 'In progress task', 'status': 'in_progress'},
            {'id': 'task3', 'content': 'Completed task', 'status': 'completed'},
            {'id': 'task4', 'content': 'Cancelled task', 'status': 'cancelled'}
        ]

        result = update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)
        assert "Successfully" in result or "saved" in result.lower()

        loaded_todos = get_todos(tmp_checkpoint)
        assert len(loaded_todos) == 4
        assert loaded_todos[0]['status'] == 'pending'
        assert loaded_todos[1]['status'] == 'in_progress'
        assert loaded_todos[2]['status'] == 'completed'
        assert loaded_todos[3]['status'] == 'cancelled'


class TestTodoMerge:
    """Todo merge operations tests."""

    def test_replace_mode(self, tmp_checkpoint):
        """Test replace mode (merge=False)."""
        # Create initial todos
        todos1 = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'pending'}
        ]
        update_todos(merge=False, todos=todos1, checkpoint_path=tmp_checkpoint)

        # Replace with new todos (minimum 2 required)
        todos2 = [
            {'id': 'task3', 'content': 'Task 3', 'status': 'in_progress'},
            {'id': 'task4', 'content': 'Task 4', 'status': 'pending'}
        ]
        update_todos(merge=False, todos=todos2, checkpoint_path=tmp_checkpoint)

        # Verify replacement
        loaded_todos = get_todos(tmp_checkpoint)
        assert len(loaded_todos) == 2
        assert loaded_todos[0]['id'] == 'task3'
        assert loaded_todos[1]['id'] == 'task4'

    def test_merge_mode(self, tmp_checkpoint):
        """Test merge mode (merge=True)."""
        # Create initial todos
        todos1 = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'pending'}
        ]
        update_todos(merge=False, todos=todos1, checkpoint_path=tmp_checkpoint)

        # Merge with new todos (minimum 2 required)
        todos2 = [
            {'id': 'task3', 'content': 'Task 3', 'status': 'in_progress'},
            {'id': 'task4', 'content': 'Task 4', 'status': 'completed'}
        ]
        update_todos(merge=True, todos=todos2, checkpoint_path=tmp_checkpoint)

        # Verify merge
        loaded_todos = get_todos(tmp_checkpoint)
        assert len(loaded_todos) == 4
        assert loaded_todos[0]['id'] == 'task1'
        assert loaded_todos[2]['id'] == 'task3'
        assert loaded_todos[3]['id'] == 'task4'

    def test_merge_update_existing(self, tmp_checkpoint):
        """Test merge mode updates existing todos by ID."""
        # Create initial todos
        todos1 = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'pending'}
        ]
        update_todos(merge=False, todos=todos1, checkpoint_path=tmp_checkpoint)

        # Update existing todos via merge (minimum 2 required)
        todos2 = [
            {'id': 'task1', 'content': 'Updated Task 1', 'status': 'completed'},
            {'id': 'task2', 'content': 'Updated Task 2', 'status': 'in_progress'}
        ]
        update_todos(merge=True, todos=todos2, checkpoint_path=tmp_checkpoint)

        # Verify update
        loaded_todos = get_todos(tmp_checkpoint)
        assert len(loaded_todos) == 2
        assert loaded_todos[0]['id'] == 'task1'
        assert loaded_todos[0]['content'] == 'Updated Task 1'
        assert loaded_todos[0]['status'] == 'completed'
        assert loaded_todos[1]['content'] == 'Updated Task 2'


class TestTodoStatusUpdate:
    """Todo status update tests."""

    def test_update_single_status(self, tmp_checkpoint):
        """Test updating a single todo status."""
        todos = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'pending'}
        ]
        update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)

        # Update status
        result = update_todo_status('task1', 'completed', tmp_checkpoint)
        assert "Successfully" in result or "updated" in result.lower()

        # Verify update
        loaded_todos = get_todos(tmp_checkpoint)
        assert loaded_todos[0]['status'] == 'completed'
        assert loaded_todos[1]['status'] == 'pending'  # Unchanged

    def test_update_status_progression(self, tmp_checkpoint):
        """Test status progression through workflow."""
        todos = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'pending'}
        ]
        update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)

        # Progress through statuses
        update_todo_status('task1', 'in_progress', tmp_checkpoint)
        loaded = get_todos(tmp_checkpoint)
        assert loaded[0]['status'] == 'in_progress'

        update_todo_status('task1', 'completed', tmp_checkpoint)
        loaded = get_todos(tmp_checkpoint)
        assert loaded[0]['status'] == 'completed'

    def test_update_nonexistent_todo(self, tmp_checkpoint):
        """Test updating non-existent todo ID."""
        todos = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'pending'}
        ]
        update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)

        # Try to update non-existent ID
        with pytest.raises(ValueError, match="not found"):
            update_todo_status('nonexistent', 'completed', tmp_checkpoint)


class TestTodoValidation:
    """Todo validation tests."""

    def test_invalid_status(self, tmp_checkpoint):
        """Test invalid status value."""
        todos = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'invalid_status'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'pending'}
        ]

        with pytest.raises(ValueError, match="Invalid status"):
            update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)

    def test_missing_required_fields(self, tmp_checkpoint):
        """Test missing required fields."""
        # Missing 'content' (need at least 2 todos)
        todos = [
            {'id': 'task1', 'status': 'pending'},
            {'id': 'task2', 'status': 'pending'}
        ]

        with pytest.raises((ValueError, KeyError, TypeError, IOError, OSError)):
            update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)

    def test_update_to_invalid_status(self, tmp_checkpoint):
        """Test updating to invalid status."""
        todos = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'pending'}
        ]
        update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)

        with pytest.raises(ValueError, match="Invalid status"):
            update_todo_status('task1', 'invalid_status', tmp_checkpoint)


class TestTodoUnicode:
    """Unicode and special character tests."""

    def test_unicode_content(self, tmp_checkpoint):
        """Test unicode in todo content."""
        todos = [
            {'id': 'task1', 'content': '完成功能实现 🎉', 'status': 'pending'},
            {'id': 'task2', 'content': 'Завершить задачу', 'status': 'in_progress'},
            {'id': 'task3', 'content': '日本語のタスク', 'status': 'completed'}
        ]

        update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)
        loaded_todos = get_todos(tmp_checkpoint)

        assert len(loaded_todos) == 3
        assert loaded_todos[0]['content'] == '完成功能实现 🎉'
        assert loaded_todos[1]['content'] == 'Завершить задачу'
        assert loaded_todos[2]['content'] == '日本語のタスク'

    def test_special_characters_in_content(self, tmp_checkpoint):
        """Test special characters in content."""
        todos = [
            {'id': 'task1', 'content': 'Fix: @#$%^&*()_+-=[]{}|;\':",./<>?', 'status': 'pending'},
            {'id': 'task2', 'content': 'Line 1\nLine 2\nLine 3', 'status': 'pending'},
            {'id': 'task3', 'content': 'Tab\tseparated\tvalues', 'status': 'pending'}
        ]

        update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)
        loaded_todos = get_todos(tmp_checkpoint)

        assert loaded_todos[0]['content'] == 'Fix: @#$%^&*()_+-=[]{}|;\':",./<>?'
        assert loaded_todos[1]['content'] == 'Line 1\nLine 2\nLine 3'
        assert loaded_todos[2]['content'] == 'Tab\tseparated\tvalues'


class TestTodoEdgeCases:
    """Edge case tests."""

    def test_very_long_content(self, tmp_checkpoint):
        """Test very long todo content."""
        long_content = "A" * 10000
        todos = [
            {'id': 'task1', 'content': long_content, 'status': 'pending'},
            {'id': 'task2', 'content': 'Normal task', 'status': 'pending'}
        ]

        update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)
        loaded_todos = get_todos(tmp_checkpoint)

        assert len(loaded_todos[0]['content']) == 10000

    def test_many_todos(self, tmp_checkpoint):
        """Test handling many todos."""
        todos = [
            {'id': f'task{i}', 'content': f'Task {i}', 'status': 'pending'}
            for i in range(1000)
        ]

        update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)
        loaded_todos = get_todos(tmp_checkpoint)

        assert len(loaded_todos) == 1000
        assert loaded_todos[0]['id'] == 'task0'
        assert loaded_todos[999]['id'] == 'task999'

    def test_duplicate_ids_in_merge(self, tmp_checkpoint):
        """Test handling duplicate IDs in merge operation."""
        todos1 = [
            {'id': 'task1', 'content': 'Original Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Original Task 2', 'status': 'pending'}
        ]
        update_todos(merge=False, todos=todos1, checkpoint_path=tmp_checkpoint)

        # Merge with duplicate ID (should update)
        todos2 = [
            {'id': 'task1', 'content': 'Updated Task 1', 'status': 'completed'},
            {'id': 'task3', 'content': 'New Task 3', 'status': 'in_progress'}
        ]
        update_todos(merge=True, todos=todos2, checkpoint_path=tmp_checkpoint)

        loaded_todos = get_todos(tmp_checkpoint)
        assert len(loaded_todos) == 3  # task1 updated, task2 unchanged, task3 added
        assert loaded_todos[0]['content'] == 'Updated Task 1'
        assert loaded_todos[0]['status'] == 'completed'
        assert loaded_todos[2]['id'] == 'task3'


class TestTodoFileOperations:
    """File I/O operation tests."""

    def test_get_nonexistent_file(self):
        """Test getting todos from non-existent file."""
        nonexistent_path = Path("/tmp/nonexistent_todos_12345.json")

        with pytest.raises(FileNotFoundError):
            get_todos(nonexistent_path)

    def test_file_persistence(self, tmp_checkpoint):
        """Test todos persist across operations."""
        todos = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'in_progress'}
        ]

        # Create todos
        update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)

        # Read multiple times
        loaded1 = get_todos(tmp_checkpoint)
        loaded2 = get_todos(tmp_checkpoint)

        assert loaded1 == loaded2
        assert len(loaded1) == 2


class TestTodoToolClass:
    """Test the TodoTool class interface (if available)."""

    @pytest.mark.skipif(TodoTool is None, reason="TodoTool not available in this module")
    def test_tool_initialization(self, tmp_checkpoint):
        """Test tool can be initialized."""
        tool = TodoTool(checkpoint_path=tmp_checkpoint)
        assert tool is not None
        assert tool._initialized is True

    @pytest.mark.skipif(TodoTool is None, reason="TodoTool not available in this module")
    def test_tool_execute_returns_result(self, tmp_checkpoint):
        """Test tool execute returns TodoResult."""
        tool = TodoTool(checkpoint_path=tmp_checkpoint)
        todos = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'pending'}
        ]

        result = tool.execute(merge=False, todos=todos)

        assert isinstance(result, TodoResult)
        assert result.success is True

    @pytest.mark.skipif(TodoTool is None, reason="TodoTool not available in this module")
    def test_tool_with_logger(self, tmp_checkpoint):
        """Test tool with custom logger."""
        import logging
        logger = logging.getLogger("test")

        tool = TodoTool(checkpoint_path=tmp_checkpoint, logger=logger)
        todos = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'pending'}
        ]
        result = tool.execute(merge=False, todos=todos)

        assert result.success is True

    @pytest.mark.skipif(TodoTool is None, reason="TodoTool not available in this module")
    def test_tool_get_todos(self, tmp_checkpoint):
        """Test tool get_todos method."""
        tool = TodoTool(checkpoint_path=tmp_checkpoint)

        # Create todos
        todos = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'pending'}
        ]
        tool.execute(merge=False, todos=todos)

        # Get todos
        result = tool.get_todos()
        assert result.success is True
        assert len(result.data) == 2

    @pytest.mark.skipif(TodoTool is None, reason="TodoTool not available in this module")
    def test_tool_update_status(self, tmp_checkpoint):
        """Test tool update_todo_status method."""
        tool = TodoTool(checkpoint_path=tmp_checkpoint)

        # Create todos
        todos = [
            {'id': 'task1', 'content': 'Task 1', 'status': 'pending'},
            {'id': 'task2', 'content': 'Task 2', 'status': 'pending'}
        ]
        tool.execute(merge=False, todos=todos)

        # Update status
        result = tool.update_todo_status(todo_id='task1', status_to='completed')
        assert result.success is True


class TestTodoPerformance:
    """Performance comparison tests."""

    def test_create_performance(self, tmp_checkpoint, benchmark=None):
        """Benchmark todo creation performance."""
        todos = [
            {'id': f'task{i}', 'content': f'Task {i}', 'status': 'pending'}
            for i in range(100)
        ]

        start = time.time()
        update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)
        elapsed = time.time() - start

        print(f"\n[{TEST_MODULE}] Create 100 todos: {elapsed:.4f}s")
        assert elapsed < 1.0  # Should complete within 1 second

    def test_read_performance(self, tmp_checkpoint):
        """Benchmark todo reading performance."""
        # Setup: create todos
        todos = [
            {'id': f'task{i}', 'content': f'Task {i}', 'status': 'pending'}
            for i in range(100)
        ]
        update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)

        # Benchmark read
        start = time.time()
        for _ in range(100):
            get_todos(tmp_checkpoint)
        elapsed = time.time() - start

        print(f"\n[{TEST_MODULE}] Read 100 todos x 100 times: {elapsed:.4f}s")
        assert elapsed < 2.0  # Should complete within 2 seconds

    def test_merge_performance(self, tmp_checkpoint):
        """Benchmark merge operation performance."""
        # Setup: create initial todos
        todos = [
            {'id': f'task{i}', 'content': f'Task {i}', 'status': 'pending'}
            for i in range(50)
        ]
        update_todos(merge=False, todos=todos, checkpoint_path=tmp_checkpoint)

        # Benchmark merge
        new_todos = [
            {'id': f'task{i}', 'content': f'Updated Task {i}', 'status': 'completed'}
            for i in range(50)
        ]

        start = time.time()
        update_todos(merge=True, todos=new_todos, checkpoint_path=tmp_checkpoint)
        elapsed = time.time() - start

        print(f"\n[{TEST_MODULE}] Merge 50 todos: {elapsed:.4f}s")
        assert elapsed < 1.0


if __name__ == "__main__":
    import argparse
    from .base import run_tests_with_report

    parser = argparse.ArgumentParser()
    parser.add_argument('--module', default='todo',
                        choices=['todo', 'todo_refactor'],
                        help='Which todo module to test')
    args = parser.parse_args()

    # Set environment variable for the test module
    os.environ['TEST_TODO_MODULE'] = args.module

    # Use module name as tool name
    tool_name = args.module

    print(f"Testing module: {args.module}")
    print(f"Report name: {tool_name}")
    print("=" * 70)

    sys.exit(run_tests_with_report(__file__, tool_name))

