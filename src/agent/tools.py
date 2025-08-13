"""Tool stubs for the decision-tree agent (scaffold only).

Each tool follows the protocol defined in `src.agent.types.Tool` and returns a
generic result payload. Implementations will be provided in a later step.
"""

from __future__ import annotations

from typing import Any

from langchain_chroma import Chroma

from .types import AgentContext


def retrieve_semantic(ctx: AgentContext, *, index: Chroma, k: int | None = None) -> dict[str, Any]:
    """Semantic retrieval using the current vector index.

    Returns a dict with keys like: {"docs": [...], "score": float}.
    """

    return {"docs": [], "score": 0.0}


def retrieve_with_filters(ctx: AgentContext, *, index: Chroma, filters: dict[str, Any] | None = None, k: int | None = None) -> dict[str, Any]:
    """Filtered retrieval using metadata inferred from the question.

    Returns a dict with keys like: {"docs": [...], "score": float, "filters": {...}}.
    """

    return {"docs": [], "score": 0.0, "filters": filters or {}}


def assess_results(ctx: AgentContext, *, docs: list[Any]) -> dict[str, Any]:
    """Assess retrieval results and produce a simple relevance score.

    Returns a dict with keys like: {"score": float, "reason": str}.
    """

    return {"score": 0.0, "reason": "not implemented"}


def generate_answer(ctx: AgentContext, *, docs: list[Any]) -> dict[str, Any]:
    """Generate a final answer from selected docs using the existing chain.

    Returns a dict with keys like: {"answer": str}.
    """

    return {"answer": None}


