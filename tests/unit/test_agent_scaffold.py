"""Unit tests for the agent scaffold (no real logic yet)."""

from __future__ import annotations

import pytest

from langchain_chroma import Chroma

from src.agent import DecisionAgent, PolicyConfig


class _TinyEF:
    def __call__(self, input):
        if isinstance(input, list):
            return [[0.0, 0.0, 0.0] for _ in input]
        return [[0.0, 0.0, 0.0]]

    # Provide the methods Chroma expects from an embedding function wrapper
    def embed_documents(self, texts):
        return [[0.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text):
        return [0.0, 0.0, 0.0]


@pytest.fixture
def dummy_index(tmp_path):
    # Provide a tiny embedding function so Chroma queries don't error
    return Chroma(persist_directory=str(tmp_path), embedding_function=_TinyEF())


def test_agent_scaffold_runs(dummy_index):
    agent = DecisionAgent(index=dummy_index, policy=PolicyConfig())
    result = agent.run("What improves longevity?")

    assert result is not None
    assert result.status in {"completed", "impossible", "max_passes", "error"}
    assert isinstance(result.trace, list)
