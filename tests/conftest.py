"""
Pytest configuration and fixtures for RAG system testing.
Following AI/MLOps best practices for model testing.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from config import get_config


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return get_config()


@pytest.fixture(scope="session") 
def temp_db_dir():
    """Create temporary directory for test databases."""
    temp_dir = tempfile.mkdtemp(prefix="rag_test_")
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def test_papers_db(temp_db_dir):
    """Provide path to test papers database."""
    return os.path.join(temp_db_dir, "test_papers.db")


@pytest.fixture(scope="function")
def isolated_test_env(temp_db_dir, monkeypatch):
    """Isolate each test with its own database."""
    test_db = os.path.join(temp_db_dir, f"test_{os.getpid()}.db")
    monkeypatch.setenv("TEST_PAPERS_DB", test_db)
    yield test_db
    if os.path.exists(test_db):
        os.remove(test_db)