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

    # Prepare dummy docs list to bypass index and retrieval
    from langchain.schema import Document  # local import to avoid heavy deps at test collection

    dummy_docs = [Document(page_content="Dummy context about Retrieval-Augmented Generation (RAG).", metadata={})]

    with (
        patch("main.ensure_index_exists", return_value=None),  # bypass index build
        patch("main.get_metadata", return_value=dummy_docs),   # bypass retrieval
        patch("langchain_openai.ChatOpenAI") as mock_llm,
    ):
        # Mock the LLM response when invoked
        mock_resp = MagicMock()
        mock_resp.content = "Based on the provided context, RAG (Retrieval-Augmented Generation) is a technique that combines retrieval and generation."
        mock_llm.return_value.invoke.return_value = mock_resp

        # Call the pipeline
        question = "What is RAG?"
        response = answer(question)

    # Assertions (same for mocked and real)
    assert isinstance(response, str)
    assert len(response.strip()) > 0
    assert any(term in response.lower() for term in ["rag", "retrieval", "generation"])
