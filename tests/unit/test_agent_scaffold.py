"""Unit tests for the agent scaffold (no real logic yet)."""

from __future__ import annotations

import pytest

from langchain_chroma import Chroma

from src.agent import DecisionAgent, PolicyConfig


@pytest.fixture
def dummy_index(tmp_path):
    # Minimal empty Chroma instance for type wiring; will be replaced in impl tests
    # Using a throwaway persist dir so we don't touch the real db
    return Chroma(persist_directory=str(tmp_path), embedding_function=None)


def test_agent_scaffold_runs(dummy_index):
    agent = DecisionAgent(index=dummy_index, policy=PolicyConfig())
    result = agent.run("What improves longevity?")

    assert result is not None
    assert result.status in {"completed", "impossible", "max_passes", "error"}
    assert isinstance(result.trace, list)


