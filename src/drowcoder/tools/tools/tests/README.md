# Tools Tests

This directory contains unit tests for all drowcoder tools (both original and refactored versions).

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

### 🎯 Method 1: Direct test execution with module selection (Recommended)

Run tests for specific tool versions using `--module` parameter:

```bash
# Test original tools
python -m src.drowcoder.tools.tests.test_load --module load
python -m src.drowcoder.tools.tests.test_attempt_completion --module attempt_completion
python -m src.drowcoder.tools.tests.test_todo --module todo
python -m src.drowcoder.tools.tests.test_write --module write
python -m src.drowcoder.tools.tests.test_search --module search
python -m src.drowcoder.tools.tests.test_search_and_replace --module search_and_replace
python -m src.drowcoder.tools.tests.test_bash --module bash

# Test refactored tools
python -m src.drowcoder.tools.tests.test_load --module load_refactor
python -m src.drowcoder.tools.tests.test_attempt_completion --module attempt_completion_refactor
python -m src.drowcoder.tools.tests.test_todo --module todo_refactor
python -m src.drowcoder.tools.tests.test_write --module write_refactor
python -m src.drowcoder.tools.tests.test_search --module search_refactor
python -m src.drowcoder.tools.tests.test_search_and_replace --module search_and_replace_refactor
```

**Features:**
- ✅ Automatic report generation with git-aware naming
- ✅ Module selection: test original vs refactored versions
- ✅ Clean interface: `--module load` → `report_load_{sha}_[dirty].log`
- ✅ Based on `base.py` for consistent formatting
- ✅ Supports relative imports (no IDE warnings)

### 🔬 Method 2: pytest with environment variable

Run tests using pytest with environment variable to select module:

```bash
# Test original tools
TEST_LOAD_MODULE=load pytest src/drowcoder/tools/tests/test_load.py -v
TEST_BASH_MODULE=bash pytest src/drowcoder/tools/tests/test_bash.py -v

# Test refactored tools
TEST_LOAD_MODULE=load_refactor pytest src/drowcoder/tools/tests/test_load.py -v
```

**Environment variable naming:**
- `TEST_LOAD_MODULE` - for load tool tests
- `TEST_TODO_MODULE` - for todo tool tests
- `TEST_BASH_MODULE` - for bash tool tests
- `TEST_SAR_MODULE` - for search_and_replace tool tests
- `TEST_SEARCH_MODULE` - for search tool tests
- (write and attempt_completion use `TEST_MODULE`)

### 🧪 Standard pytest options

```bash
# Run all tests (no auto-report)
pytest src/drowcoder/tools/tests/ -v --no-cov

# Run specific tool tests
pytest src/drowcoder/tools/tests/test_load.py -v
pytest src/drowcoder/tools/tests/test_write.py -v
pytest src/drowcoder/tools/tests/test_bash.py -v
```

## Test Coverage

Currently tested tools:
- ✅ `attempt_completion` - 31 tests
- ✅ `load` - 34 tests
- ✅ `todo` - 29 tests
- ✅ `write` - 48 tests
- ✅ `search` - 38 tests
- ✅ `search_and_replace` - 32 tests
- ✅ `bash` - 29 tests

Total: **~240+ tests**, all passing ✅

**Note:** Some tests may be skipped for original versions if they test BaseTool-specific features (logger, callback) that are only available in refactored versions.

## Test Categories

Each tool test file includes:
1. **Basic functionality tests** - Core feature validation
2. **Edge case tests** - Boundary conditions and special cases
3. **Unicode tests** - International character support
4. **Error handling tests** - Error conditions and exceptions
5. **Tool class interface tests** - BaseTool interface validation (refactored versions)
6. **Parametrized tests** - Multiple inputs tested efficiently
7. **Output format tests** - Different output styles and formats

**Important:** Test files are designed to work with both original and refactored versions. They dynamically import the appropriate module based on environment variables or command-line arguments.

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

```bash
pip install pytest pytest-cov
```

## Testing Strategy

All test files support testing both original and refactored versions:

1. **Dynamic module loading** - Tests import the appropriate module based on environment variables
2. **Identical test cases** - Same tests run against both versions to ensure functional equivalence
3. **BaseTool-aware** - Tests detect if tool supports BaseTool features (logger, callback) and skip gracefully
4. **Automatic reporting** - Git-aware test reports generated automatically

## Notes

- Test reports are saved to `reports/` directory with git commit SHA and dirty status
- Original tool versions may skip some BaseTool-specific tests
- All refactored tools maintain 100% functional compatibility with original versions

