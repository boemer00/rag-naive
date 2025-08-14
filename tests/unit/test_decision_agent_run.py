"""Tests for the decision-tree agent run behavior."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from langchain_chroma import Chroma

from src.agent.decision_tree import DecisionAgent
from src.agent.policy import PolicyConfig

# Reuse tiny embedding fixture utilities from scaffold tests
from tests.unit.test_agent_scaffold import _TinyEF  # noqa: F401


@pytest.fixture
def dummy_index(tmp_path) -> Chroma:
    return Chroma(persist_directory=str(tmp_path), embedding_function=_TinyEF())


def _add_docs(index: Chroma) -> None:
    texts = [
        "Regular aerobic exercise improves VO2 max and cardiovascular fitness.",
        "Meta-analysis shows nutrition and training can impact longevity markers.",
    ]
    metadatas = [
        {"study_type": "observational"},
        {"study_type": "meta-analysis"},
    ]
    index.add_texts(texts=texts, metadatas=metadatas)


def test_decision_agent_happy_path(monkeypatch: Any, dummy_index: Chroma) -> None:
    # Ensure config has API key and mock LLM
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class _FakeResp:
        def __init__(self, content: str) -> None:
            self.content = content

    class _FakeLLM:
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            pass

        def invoke(self, _prompt: str) -> _FakeResp:
            return _FakeResp("Mocked final answer")

    # Patch ChatOpenAI used in generate_answer
    import src.agent.tools as tools

    monkeypatch.setattr(tools, "ChatOpenAI", _FakeLLM)

    _add_docs(dummy_index)
    agent = DecisionAgent(index=dummy_index, policy=PolicyConfig())
    result = agent.run("What improves VO2 max the fastest?")

    assert result is not None
    assert result.status in {"completed", "impossible"}
    assert isinstance(result.trace, list) and len(result.trace) > 0
    if result.status == "completed":
        assert isinstance(result.answer, str) and len(result.answer) > 0


def test_decision_agent_low_relevance_impossible(monkeypatch: Any, tmp_path) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Empty index will yield low scores across passes
    index = Chroma(persist_directory=str(tmp_path), embedding_function=_TinyEF())

    # Mock LLM to be safe, even if we likely never call it
    class _FakeLLM:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def invoke(self, _prompt: str) -> Any:
            class _R:
                content = ""

            return _R()

    import src.agent.tools as tools

    monkeypatch.setattr(tools, "ChatOpenAI", _FakeLLM)

    strict_policy = PolicyConfig(
        min_relevance_score=0.99,
        enable_filtered_retry=True,
        enable_semantic_retry=True,
    )

    agent = DecisionAgent(index=index, policy=strict_policy)
    result = agent.run("Unrelated query that should not match anything")

    assert result is not None
    assert result.status in {"completed", "impossible"}
    assert isinstance(result.trace, list) and len(result.trace) > 0
    # With empty index and strict threshold, should be impossible
    assert result.status == "impossible"



