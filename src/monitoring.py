import os
import json
import random
import warnings
from typing import Optional, Callable, Any

# Graceful LangSmith import
try:
    from langsmith import traceable, Client
    from langsmith.run_helpers import get_current_run_tree
    LANGSMITH_AVAILABLE = True
except ImportError:
    def traceable(fn):  # no-op decorator
        return fn
    Client = None
    get_current_run_tree = None
    LANGSMITH_AVAILABLE = False


def configure_langsmith(project_name: Optional[str] = None) -> None:
    """Setup LangSmith if available."""
    if not LANGSMITH_AVAILABLE:
        warnings.warn("LangSmith not installed - tracing disabled")
        return

    if project_name:
        os.environ.setdefault("LANGSMITH_PROJECT", project_name)
    os.environ.setdefault("LANGSMITH_TRACING", "true")


def evaluate_rag(question: str, answer: str, context: str) -> dict[str, float]:
    """Grade RAG response quality using LLM judge."""
    if not LANGSMITH_AVAILABLE:
        return {}

    # Early exit if not sampled
    from config import get_config
    config = get_config()
    if random.random() > config.eval_sample_rate:
        return {}

    # Only import heavy dependencies if we're actually evaluating
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        model=config.eval_model,
        temperature=0,
        max_tokens=200,
        openai_api_key=config.openai_api_key
    )

    prompt = f"""Evaluate this RAG system response on four metrics (0.0-1.0 scale, 1.0 = perfect):

QUESTION: {question}

ANSWER: {answer}

CONTEXT: {context}

Rate each metric:
- faithfulness: How well is the answer grounded in/supported by the context?
- answer_relevance: How relevant is the answer to the question asked?
- context_relevance: How relevant is the retrieved context to the question?
- context_recall: How well does the context cover the information needed to answer the question?

Respond with ONLY a JSON object in this format:
{{"faithfulness": 0.XX, "answer_relevance": 0.XX, "context_relevance": 0.XX, "context_recall": 0.XX}}"""

    try:
        response = llm.invoke(prompt)
        # Handle LLM responses that might be wrapped in markdown code blocks
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        if content.startswith("```"):
            content = content[3:]   # Remove ```
        if content.endswith("```"):
            content = content[:-3]  # Remove closing ```
        content = content.strip()

        scores = json.loads(content)
        return {k: max(0, min(1, float(v))) for k, v in scores.items()}
    except Exception as exc:
        warnings.warn(f"RAG evaluation failed: {exc}")
        return {}


def send_rag_feedback(scores: dict[str, float]) -> None:
    """Send evaluation scores as LangSmith feedback."""
    if not scores or not LANGSMITH_AVAILABLE or not get_current_run_tree:
        return

    run = get_current_run_tree()
    if not run:
        return

    try:
        client = Client()
        for metric, score in scores.items():
            client.create_feedback(str(run.id), key=metric, score=score)
    except Exception as exc:
        warnings.warn(f"Failed to send feedback: {exc}")


def evaluate_and_log(question: str, answer: str, context: str) -> None:
    """Evaluate RAG response and send feedback to LangSmith."""
    scores = evaluate_rag(question, answer, context)
    send_rag_feedback(scores)


def trace_run(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Lightweight tracing decorator - just wraps @traceable."""
    if not LANGSMITH_AVAILABLE:
        return fn
    return traceable(fn)
