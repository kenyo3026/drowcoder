# Tools Tests

This directory contains unit tests for all drowcoder built-in tools.

## Directory Structure

```
tests/
├── __init__.py                     # Package initialization
├── conftest.py                     # Pytest fixtures and session hooks
├── base.py                         # Base utilities for report generation
├── test_attempt_completion.py      # Tests for attempt_completion tool
├── test_load.py                    # Tests for load tool
├── test_todo.py                    # Tests for todo tool
├── test_write.py                   # Tests for write tool
├── test_search.py                  # Tests for search tool
├── test_search_and_replace.py      # Tests for search_and_replace tool
├── test_bash.py                    # Tests for bash tool
├── reports/                        # Test reports (auto-generated)
│   └── report_*.log                 # Git-aware test reports
└── README.md                       # This file
```

## Running Tests

### 🎯 Method 1: Using pytest (Recommended)

Run tests using pytest:

```bash
# Run all tool tests
pytest src/drowcoder/tools/tools/tests/ -v

# Run specific tool tests
pytest src/drowcoder/tools/tools/tests/test_load.py -v
pytest src/drowcoder/tools/tools/tests/test_write.py -v
pytest src/drowcoder/tools/tools/tests/test_bash.py -v
pytest src/drowcoder/tools/tools/tests/test_search.py -v
pytest src/drowcoder/tools/tools/tests/test_search_and_replace.py -v
pytest src/drowcoder/tools/tools/tests/test_todo.py -v
pytest src/drowcoder/tools/tools/tests/test_attempt_completion.py -v

# Run with coverage
pytest src/drowcoder/tools/tools/tests/ -v --cov=src/drowcoder/tools/tools --cov-report=html
```

### 🔬 Method 2: Direct test execution with auto-report

Run tests directly to generate git-aware reports:

```bash
# Run individual tool tests with automatic report generation
python -m src.drowcoder.tools.tools.tests.test_load
python -m src.drowcoder.tools.tools.tests.test_write
python -m src.drowcoder.tools.tools.tests.test_bash
python -m src.drowcoder.tools.tools.tests.test_search
python -m src.drowcoder.tools.tools.tests.test_search_and_replace
python -m src.drowcoder.tools.tools.tests.test_todo
python -m src.drowcoder.tools.tools.tests.test_attempt_completion
```

**Features:**
- ✅ Automatic report generation with git-aware naming
- ✅ Clean interface: generates `report_{tool}_{sha}_[dirty].log`
- ✅ Based on `base.py` for consistent formatting
- ✅ Reports saved to `reports/` directory


## Test Categories

Each tool test file includes:
1. **Basic functionality tests** - Core feature validation
2. **Edge case tests** - Boundary conditions and special cases
3. **Unicode tests** - International character support
4. **Error handling tests** - Error conditions and exceptions
5. **Tool class interface tests** - BaseTool interface validation
6. **Parametrized tests** - Multiple inputs tested efficiently
7. **Output format tests** - Different output styles and formats

## Key Files

### `base.py`
Provides common utilities for test report generation:
- `get_git_info()` - Get git commit SHA and dirty status
- `generate_report_name()` - Generate git-aware report filenames
- `run_tests_with_report()` - Run tests and generate reports automatically

Used by all test files for consistent report generation.

### `conftest.py`
Pytest configuration file:
- Provides `tmp_path` fixture for temporary directories
- `pytest_sessionfinish` hook for automatic report generation (alternative method)

## Requirements

### Installation

The test dependencies are already configured in `pyproject.toml`. Install them using one of the following methods:

**Method 1: Install test dependencies (Recommended)**
```bash
pip install -e ".[test]"
```

**Method 2: Install all development dependencies**
```bash
pip install -e ".[dev]"
```

**Method 3: Install from requirements.txt**
```bash
pip install -r requirements.txt
```

### Dependencies
- pytest>=7.0.0
- pytest-cov>=4.0.0
- pytest-mock>=3.0.0 (optional, for advanced mocking)

## Testing Strategy

All test files follow a unified testing approach:

1. **Direct imports** - Tests import tools directly from `drowcoder.tools.tools`
2. **Comprehensive coverage** - Each tool has extensive test coverage for all features
3. **BaseTool interface** - All tools implement the unified BaseTool interface
4. **Automatic reporting** - Git-aware test reports generated automatically when running directly

## Notes

- Test reports are saved to `reports/` directory with git commit SHA and dirty status
- All tools implement the unified BaseTool architecture
- Tests validate both functionality and BaseTool interface compliance

