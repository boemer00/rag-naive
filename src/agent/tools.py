"""Tool stubs for the decision-tree agent (scaffold only).

Each tool follows the protocol defined in `src.agent.types.Tool` and returns a
generic result payload. Implementations will be provided in a later step.
"""

from __future__ import annotations

from typing import Any

from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI

from config import get_config
from src.chain import PROMPT_RAG

from .types import AgentContext


def _infer_filters_from_question(question: str) -> dict[str, Any]:
    """Infer simple metadata filters from the user's question.

    This implementation keeps to exact-match filters that work reliably with
    Chroma's metadata filtering. Topic/biomarker signals are appended to the
    query string by the caller rather than used as strict filters since those
    fields are stored as comma-separated strings in the current index.
    """

    q = question.lower()
    study_type: str | None = None

    if any(w in q for w in ["meta-analysis", "systematic review"]):
        study_type = "meta-analysis"
    elif any(w in q for w in ["randomized", "rct", "clinical trial"]):
        study_type = "rct"
    elif any(w in q for w in ["cohort", "observational", "longitudinal"]):
        study_type = "observational"

    filters: dict[str, Any] = {}
    if study_type:
        filters["study_type"] = study_type

    return filters


def _score_docs(question: str, docs: list[Document]) -> float:
    """Heuristic score for retrieval quality.

    Combines: number of docs, total content length, and keyword overlap.
    Returns score in [0, 1].
    """

    if not docs:
        return 0.0

    q = question.lower()
    length_score = min(1.0, sum(len(d.page_content) for d in docs) / 4000.0)

    # crude keyword overlap based on top tokens
    keywords = [
        w for w in q.replace("?", " ").replace(",", " ").split() if len(w) > 3
    ][:8]
    if not keywords:
        overlap_score = 0.3
    else:
        hits = 0
        sample_text = "\n".join(d.page_content for d in docs)[:4000].lower()
        for w in keywords:
            if w in sample_text:
                hits += 1
        overlap_score = min(1.0, hits / max(1, len(keywords)))

    count_score = min(1.0, len(docs) / 6.0)

    return max(0.0, min(1.0, 0.4 * length_score + 0.4 * overlap_score + 0.2 * count_score))


def retrieve_semantic(ctx: AgentContext, *, index: Chroma, k: int | None = None) -> dict[str, Any]:
    """Semantic retrieval using the current vector index.

    Returns: {"docs": list[Document], "score": float}
    """

    if k is None:
        k = int(ctx.config.get("retrieval_k", 6))

    retriever = index.as_retriever(search_type="similarity", search_kwargs={"k": k})
    docs: list[Document] = retriever.invoke(ctx.question)
    score = _score_docs(ctx.question, docs)
    return {"docs": docs, "score": score}


def retrieve_with_filters(ctx: AgentContext, *, index: Chroma, filters: dict[str, Any] | None = None, k: int | None = None) -> dict[str, Any]:
    """Filtered retrieval using simple metadata filters and query augmentation.

    Returns: {"docs": list[Document], "score": float, "filters": dict}
    """

    if k is None:
        k = int(ctx.config.get("retrieval_k", 6))

    effective_filters = filters or _infer_filters_from_question(ctx.question)

    # Augment the question with likely topic/biomarker hints for better recall
    q = ctx.question
    lower = q.lower()
    augment_terms: list[str] = []
    topic_map = {
        "cardiovascular": ["cardiovascular", "heart", "blood pressure"],
        "sleep": ["sleep", "circadian"],
        "exercise": ["exercise", "training", "fitness"],
        "nutrition": ["nutrition", "diet", "caloric"],
        "longevity": ["longevity", "aging", "lifespan"],
    }
    biomarkers = {"vo2_max": ["vo2", "oxygen consumption"], "heart_rate": ["resting heart"], "blood_pressure": ["blood pressure"], "sleep_metrics": ["sleep"]}

    for key, words in {**topic_map, **biomarkers}.items():
        if any(w in lower for w in words):
            augment_terms.append(key)

    augmented_query = q if not augment_terms else f"{q} {' '.join(set(augment_terms))}"

    # Use Chroma similarity_search with metadata filters when available
    docs: list[Document] = index.similarity_search(augmented_query, k=k, filter=effective_filters or None)
    score = _score_docs(ctx.question, docs)
    return {"docs": docs, "score": score, "filters": effective_filters}


def assess_results(ctx: AgentContext, *, docs: list[Any]) -> dict[str, Any]:
    """Assess retrieval results and produce a simple relevance score."""

    score = _score_docs(ctx.question, docs)
    reason = "insufficient context" if score < float(ctx.config.get("min_relevance_score", 0.5)) else "sufficient context"
    return {"score": score, "reason": reason}


def generate_answer(ctx: AgentContext, *, docs: list[Any]) -> dict[str, Any]:
    """Generate a final answer from selected docs using PROMPT_RAG and ChatOpenAI."""

    if not docs:
        return {"answer": None}

    config = get_config()
    context_text = "\n\n".join(d.page_content for d in docs)

    prompt = PromptTemplate(input_variables=["context", "question"], template=PROMPT_RAG)
    formatted = prompt.format(context=context_text, question=ctx.question)

    llm = ChatOpenAI(
        model=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        openai_api_key=config.openai_api_key,
    )
    response = llm.invoke(formatted)
    return {"answer": response.content if hasattr(response, "content") else str(response)}
