"""
Pytest configuration and fixtures for agent tests.

This module provides:
- tmp_workspace fixture for temporary workspace directories
- pytest_sessionfinish hook for automatic report generation
"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def tmp_workspace():
    """
    Create a temporary workspace directory for agent tests.

    This fixture creates a temporary directory that can be used as
    a workspace for DrowAgent instances during testing.
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)

