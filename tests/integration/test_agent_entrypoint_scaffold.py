"""Integration-level scaffold: ensure we can construct an agent from current index."""

from __future__ import annotations

import pytest

from src.indexer import ensure_index_exists
from src.utils import load_source_docs
from src.agent import DecisionAgent


@pytest.mark.integration
def test_construct_agent_from_index():
    # Build or load the existing index (side-effect: reads local pdfs)
    index = ensure_index_exists(load_source_docs, force=False)

    agent = DecisionAgent(index=index)
    result = agent.run("What factors influence longevity?")

    # We only assert shape, not content, since there's no implementation yet
    assert hasattr(result, "status")
    assert hasattr(result, "trace")


