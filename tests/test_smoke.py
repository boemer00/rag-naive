"""Integration smoke test for the RAG pipeline.

This test validates that the end-to-end RAG pipeline can:
1. Load and index documents
2. Process a simple question
3. Generate a non-empty response
"""

import os
from unittest.mock import patch, MagicMock
import pytest

from main import answer


@pytest.mark.integration
def test_rag_pipeline_smoke() -> None:
    """Test that the RAG pipeline can generate a response without errors."""

    # Mock OpenAI API if no key is available
    if not os.getenv("OPENAI_API_KEY"):
        with patch("langchain_openai.ChatOpenAI") as mock_llm:
            # Mock the LLM response
            mock_response = MagicMock()
            mock_response.content = "Based on the provided context, RAG (Retrieval-Augmented Generation) is a technique that combines retrieval and generation."
            mock_llm.return_value.invoke.return_value = mock_response

            # Test the pipeline
            question = "What is RAG?"
            response = answer(question)

            # Assertions
            assert isinstance(response, str)
            assert len(response.strip()) > 0
            assert "RAG" in response or "retrieval" in response.lower()

    else:
        # Real test with OpenAI API
        question = "What is RAG?"
        response = answer(question)

        # Assertions
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        # Basic sanity check that response mentions relevant terms
        response_lower = response.lower()
        assert any(term in response_lower for term in ["rag", "retrieval", "generation", "augment"])
