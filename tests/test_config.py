"""
Test configuration and mocking utilities.
Handles API mocking and test environment setup.
"""

import os
from unittest.mock import Mock, patch

import pytest


class MockOpenAIEmbeddings:
    """Mock OpenAI embeddings for testing."""

    def __init__(self, **kwargs):
        self.model = kwargs.get('model', 'text-embedding-3-large')

    def embed_documents(self, texts):
        """Return mock embeddings for documents."""
        return [[0.1 + i * 0.01] * 3072 for i, _ in enumerate(texts)]

    def embed_query(self, text):
        """Return mock embedding for query."""
        return [0.1] * 3072


class MockChatOpenAI:
    """Mock OpenAI chat model for testing."""

    def __init__(self, **kwargs):
        self.model = kwargs.get('model', 'gpt-4')
        self.temperature = kwargs.get('temperature', 0.0)

    def invoke(self, prompt):
        """Return mock response."""
        mock_response = Mock()
        mock_response.content = "This is a mock response for testing purposes."
        return mock_response


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment with proper mocking."""
    # Disable LangSmith during tests
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    # Set test OpenAI key if not provided
    if not os.getenv("OPENAI_API_KEY"):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-for-testing")

    # Mock OpenAI classes to avoid API calls in most tests
    with patch('langchain_openai.OpenAIEmbeddings', MockOpenAIEmbeddings):
        with patch('langchain_openai.ChatOpenAI', MockChatOpenAI):
            yield


@pytest.fixture
def mock_openai_components():
    """Provide mocked OpenAI components for tests that need them."""
    return {
        'embeddings': MockOpenAIEmbeddings(),
        'chat': MockChatOpenAI()
    }
