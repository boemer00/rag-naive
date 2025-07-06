"""LangSmith monitoring utilities (scaffold).

This module centralises all interactions with LangSmith for tracing
and observability. Implementation to be provided in the next step."""
from __future__ import annotations

import os
import warnings
from functools import wraps
import json
from typing import Callable, TypeVar, Any, Optional

from config import get_openai_api_key

from src.indexer import ensure_index_exists  # local evaluation reuse
from src.utils import load_source_docs
from src.retrieval import get_metadata
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

# Attempt to import LangSmith SDK. Gracefully degrade if unavailable so that
# the application can still run locally without the extra dependency.
try:
    from langsmith import traceable, Client  # type: ignore
    _LANGSMITH_AVAILABLE = True
except ImportError:  # pragma: no cover – safeguard when dependency missing
    # Fallback stubs when langsmith is not installed.
    traceable = None  # type: ignore
    Client = None  # type: ignore
    _LANGSMITH_AVAILABLE = False

# Generic type variable for decorator typings
F = TypeVar("F", bound=Callable[..., Any])

# Internal state guard to ensure idempotent configuration
_configured: bool = False
_client: Optional["Client"] = None  # type: ignore[name-defined]

_EVAL_ENABLED = os.getenv("EVAL_RAG_METRICS", "true").lower() == "true"

# Attempt to import utility to access current RunTree when LangSmith v2 tracing is enabled.
try:
    from langsmith.run_helpers import get_current_run_tree as _get_current_run_tree  # type: ignore
except Exception:  # pragma: no cover
    _get_current_run_tree = None  # type: ignore

# ---------------------------------------------------------------------------
# Heuristic LLM-based grader (simple prompt) ---------------------------------
# ---------------------------------------------------------------------------

_GRADE_PROMPT = PromptTemplate(
    input_variables=["question", "answer", "context"],
    template=(
        "You are evaluating the quality of a Retrieval-Augmented Generation (RAG) response.\n"
        "Assess the following dimensions and return JSON with four float scores (0-1, 1=best).\n"
        "Keys: faithfulness, answer_relevance, context_relevance, context_recall.\n\n"
        "Question: {question}\n\n"
        "Answer: {answer}\n\n"
        "Context: {context}\n\n"
        "Respond **ONLY** with a JSON dict, no explanation."
    ),
)


def _grade_rag(question: str, answer: str, context: str) -> dict[str, float]:
    """Call a lightweight LLM judge to produce metric scores."""

    llm = ChatOpenAI(
        model=os.getenv("RAG_EVAL_MODEL", "gpt-3.5-turbo-0125"),
        temperature=0.0,
        max_tokens=256,
        openai_api_key=get_openai_api_key(),
    )

    prompt = _GRADE_PROMPT.format(question=question, answer=answer, context=context)
    try:
        resp = llm.invoke(prompt)
        parsed = json.loads(resp.content)
        # Ensure keys exist and are floats in 0-1
        return {
            k: max(0.0, min(1.0, float(parsed.get(k, 0))))
            for k in (
                "faithfulness",
                "answer_relevance",
                "context_relevance",
                "context_recall",
            )
        }
    except Exception as exc:
        warnings.warn(f"RAG metric grading failed: {exc}")
        return {}


# ---------------------------------------------------------------------------
# Decorator wrapper extension ------------------------------------------------
# ---------------------------------------------------------------------------


def configure_langsmith(project_name: Optional[str] = None) -> None:
    """Configure LangSmith tracing.

    This helper is idempotent – calling it multiple times is safe.
    If the LangSmith SDK is not available (e.g. in open-source clones of this
    repo), the function becomes a no-op and prints a gentle warning.

    Parameters
    ----------
    project_name : Optional[str]
        Optional project name to set/override via ``LANGSMITH_PROJECT``.
    """
    global _configured

    if _configured:  # Already configured – skip further processing
        return

    if not _LANGSMITH_AVAILABLE:
        warnings.warn(
            "LangSmith SDK not installed. Monitoring disabled. "
            "Install it with `pip install langsmith` to enable tracing.",
            RuntimeWarning,
        )
        _configured = True
        return

    # Ensure minimal env vars are present to activate tracing.
    if project_name:
        os.environ.setdefault("LANGSMITH_PROJECT", project_name)

    os.environ.setdefault("LANGSMITH_TRACING", "true")

    # Activate new v2 tracing so we can access the current RunTree inside
    # the decorated function (needed to attach feedback programmatically).
    os.environ.setdefault("LANGSMITH_TRACING_V2", "true")

    # Optional: provide default public endpoint if not specified.
    os.environ.setdefault("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

    # Check for critical vars. If missing we don't raise – we disable tracing.
    required = ["LANGSMITH_API_KEY"]
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        warnings.warn(
            "Missing LangSmith environment variables: " + ", ".join(missing) +
            ". Tracing is disabled until they are provided.",
            RuntimeWarning,
        )
        os.environ["LANGSMITH_TRACING"] = "false"

    _configured = True


def _get_client() -> Optional["Client"]:  # type: ignore[name-defined]
    """Lazily create and cache a LangSmith Client instance (if available)."""
    global _client

    if not _LANGSMITH_AVAILABLE:
        return None

    if _client is None:
        _client = Client()  # type: ignore[call-arg]
    return _client


def trace_run(fn: F) -> F:  # type: ignore[override]
    """Lightweight decorator that records function inputs/outputs.

    If LangSmith is available and tracing is enabled, we wrap the function with
    ``@langsmith.traceable``. Otherwise, the original function is returned
    untouched.
    """

    if not _LANGSMITH_AVAILABLE:
        # SDK not installed – return original function unmodified.
        return fn  # type: ignore[return-value]

    # Apply the ``@traceable`` decorator provided by LangSmith. We also use
    # ``wraps`` to preserve the original function's metadata.

    @wraps(fn)
    @traceable  # type: ignore[misc]
    def _wrapper(*args: Any, **kwargs: Any):  # type: ignore[override]  # noqa: ANN401
        result = fn(*args, **kwargs)

        # Optional inline evaluation for RAG metrics
        if _EVAL_ENABLED and _LANGSMITH_AVAILABLE:
            try:
                question = args[0] if args else kwargs.get("question", "")
                # Recompute context using retrieval helper (cheap)
                from src.indexer import ensure_index_exists  # local import to avoid cycles
                from src.utils import load_source_docs
                from src.retrieval import get_metadata

                index = ensure_index_exists(load_source_docs)
                docs = get_metadata(index, question, k=6)
                context_str = "\n\n".join(d.page_content for d in docs)

                scores = _grade_rag(str(question), str(result), context_str)

                # Attach scores as Feedback entries to the *current* run.
                if scores and _get_current_run_tree is not None:
                    run = _get_current_run_tree()
                    if run is not None:
                        run_id = str(run.id)
                        cl = _get_client()
                        if cl:
                            for key, val in scores.items():
                                cl.create_feedback(run_id, key=key, score=val)
            except Exception as exc:
                warnings.warn(f"Inline RAG evaluation failed: {exc}")

        return result

    return _wrapper  # type: ignore[return-value]


# Expose the client as a module-level attribute for convenience.
client: Optional["Client"] = _get_client()  # type: ignore[name-defined]
