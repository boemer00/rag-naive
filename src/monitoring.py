"""LangSmith monitoring utilities (scaffold).

This module centralises all interactions with LangSmith for tracing
and observability. Implementation to be provided in the next step."""
from __future__ import annotations

import os
import warnings
from functools import wraps
from typing import Callable, TypeVar, Any, Optional

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
        return fn(*args, **kwargs)

    return _wrapper  # type: ignore[return-value]


# Expose the client as a module-level attribute for convenience.
client: Optional["Client"] = _get_client()  # type: ignore[name-defined]
