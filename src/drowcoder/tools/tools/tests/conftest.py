"""
Pytest configuration and fixtures for tool tests.

This module provides:
- tmp_path fixture for temporary directories
- pytest_sessionfinish hook for automatic report generation
"""

import pytest
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


@pytest.fixture
def tmp_path():
    """
    Create a temporary directory for test files.

    This fixture is used extensively in test_load.py for creating
    temporary test files during testing.
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


def pytest_sessionfinish(session, exitstatus):
    """
    Generate test report after test session completes.

    This hook is called after all tests have been run and the session is about to finish.
    """
    from .base import get_git_info, generate_report_name

    # Get git info
    commit_sha, is_dirty, git_available = get_git_info()

    # Determine tool name from test file
    test_files = []
    for item in session.items:
        test_file = Path(item.fspath)
        if test_file not in test_files:
            test_files.append(test_file)

    # Generate report for each test file
    reports_dir = Path(__file__).parent / 'reports'
    reports_dir.mkdir(exist_ok=True)

    for test_file in test_files:
        if test_file.stem.startswith('test_'):
            tool_name = test_file.stem.replace('test_', '')
            report_name = generate_report_name(tool_name, commit_sha, is_dirty)
            report_path = reports_dir / report_name

            # Create report header
            header = f"""{'=' * 70}
Test Report
{'=' * 70}
Tool: {tool_name}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Git Commit: {commit_sha if git_available else 'N/A'}
Working Dir: {'dirty (uncommitted changes)' if is_dirty else 'clean'}
Exit Code: {exitstatus}
Test File: {test_file.name}
{'=' * 70}

Test session completed.
Total tests: {len([item for item in session.items if Path(item.fspath) == test_file])}
Exit status: {exitstatus}
"""

            # Write report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(header)

            print(f"\n📄 Report saved: {report_path}")

