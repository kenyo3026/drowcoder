"""
Base utilities for test report generation.

This module provides common functionality for all test files to generate
consistent reports with git-aware naming.

Key Functions:
- get_git_info(): Get git commit SHA and dirty status
- generate_report_name(): Generate git-aware report filenames
- run_tests_with_report(): Run pytest and generate reports automatically

Usage:
    All test files use this module via:
    ```python
    from .base import run_tests_with_report
    sys.exit(run_tests_with_report(__file__, 'tool_name'))
    ```

This ensures consistent report generation across all tool tests.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional


def get_git_info() -> Tuple[Optional[str], bool, bool]:
    """
    Get current git commit SHA and dirty status.

    Returns:
        tuple: (commit_sha8, is_dirty, git_available)
            - commit_sha8: 8-character commit SHA, or None if git unavailable
            - is_dirty: True if working directory has uncommitted changes
            - git_available: True if git is available and in a git repo
    """
    try:
        # Get current commit SHA (8 characters)
        result = subprocess.run(
            ['git', 'rev-parse', '--short=8', 'HEAD'],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        commit_sha = result.stdout.strip()

        # Check if working directory is dirty
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        is_dirty = bool(result.stdout.strip())

        return commit_sha, is_dirty, True

    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None, False, False


def generate_report_name(tool_name: str, commit_sha: Optional[str], is_dirty: bool, extension: str = 'log') -> str:
    """
    Generate report filename based on git status.

    Args:
        tool_name: Name of the tool being tested
        commit_sha: Git commit SHA (8 chars), or None
        is_dirty: Whether working directory has uncommitted changes
        extension: File extension (default: 'log')

    Returns:
        str: Report filename

    Examples:
        - Clean repo: report_load_0ada4013.log
        - Dirty repo: report_load_0ada4013_dirty.log
        - No git: report_load.log
    """
    if commit_sha:
        dirty_suffix = '_dirty' if is_dirty else ''
        return f"report_{tool_name}_{commit_sha}{dirty_suffix}.{extension}"
    else:
        # Fallback: simple name if git not available
        return f"report_{tool_name}.{extension}"


def run_tests_with_report(test_file: str, tool_name: str) -> int:
    """
    Run pytest tests and generate a report with git-aware naming.

    This function should be called from the `if __name__ == "__main__"` block
    of each test file to enable automatic report generation.

    Args:
        test_file: Path to the test file (__file__)
        tool_name: Name of the tool being tested (e.g., 'attempt_completion', 'load')

    Returns:
        int: Exit code from pytest (0 = success, non-zero = failure)

    Example:
        if __name__ == "__main__":
            from test_base import run_tests_with_report
            sys.exit(run_tests_with_report(__file__, 'attempt_completion'))
    """
    # Get git info
    commit_sha, is_dirty, git_available = get_git_info()

    # Generate report name
    report_name = generate_report_name(tool_name, commit_sha, is_dirty)

    # Setup reports directory
    test_path = Path(test_file)
    reports_dir = test_path.parent / 'reports'
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / report_name

    # Print git status
    if git_available:
        print(f"Git commit: {commit_sha}")
        print(f"Working directory: {'dirty (uncommitted changes)' if is_dirty else 'clean'}")
    else:
        print("Git not available, using timestamp-based naming")
    print(f"Report will be saved to: {report_path}")
    print("=" * 70)
    print()

    # Run pytest and capture output
    result = subprocess.run(
        ['pytest', test_file, '-v', '--tb=short', '--no-cov'],
        capture_output=True,
        text=True
    )

    # Generate report header
    header = f"""{'=' * 70}
Test Report
{'=' * 70}
Tool: {tool_name}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Git Commit: {commit_sha if git_available else 'N/A'}
Working Dir: {'dirty (uncommitted changes)' if is_dirty else 'clean'}
Exit Code: {result.returncode}
{'=' * 70}

"""

    # Write report to file
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(result.stdout)
        if result.stderr:
            f.write("\n\n=== STDERR ===\n" + result.stderr)

    # Print to console
    print(result.stdout)
    if result.stderr:
        print("\n=== STDERR ===")
        print(result.stderr)

    # Print report location
    print()
    print("=" * 70)
    if result.returncode == 0:
        print(f"✅ All tests passed!")
    else:
        print(f"❌ Some tests failed (exit code: {result.returncode})")
    print(f"📄 Report saved: {report_path}")
    print("=" * 70)

    return result.returncode


# For compatibility with run_tests.py
__all__ = ['get_git_info', 'generate_report_name', 'run_tests_with_report']

