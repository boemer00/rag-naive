"""
Pytest configuration and fixtures for RAG system testing.
Following AI/MLOps best practices for model testing.
"""

import os
import shutil
import tempfile

import pytest

from config import get_config

# Import test configuration
pytest_plugins = ["tests.test_config"]


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


@pytest.fixture(scope="session", autouse=True)
def disable_langsmith():
    """Disable LangSmith during testing to avoid authentication issues."""
    os.environ["LANGSMITH_TRACING"] = "false"
    # Remove any existing LangSmith keys during testing
    os.environ.pop("LANGSMITH_API_KEY", None)
