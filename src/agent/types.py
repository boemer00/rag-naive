"""Type definitions for the decision-tree agent (scaffold only).

No implementation logic is provided in this step.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Protocol


StopReason = Literal["completed", "impossible", "max_passes", "error"]


@dataclass
class AgentContext:
    """Execution context for the agent.

    Attributes
    ----------
    question: The user question being answered.
    config: Arbitrary configuration map (e.g., retrieval k, thresholds).
    trace_enabled: Whether to collect per-node traces for UI/telemetry.
    """

    question: str
    config: dict[str, Any] = field(default_factory=dict)
    trace_enabled: bool = True


@dataclass
class AgentNodeTrace:
    """Trace entry for a single decision-tree node.

    Fields are intentionally generic to allow various tools to report useful
    diagnostics without leaking sensitive internals.
    """

    node_id: str
    name: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    decision: str | None = None


@dataclass
class AgentResult:
    """Aggregate result returned by the agent."""

    answer: str | None
    status: StopReason
    trace: list[AgentNodeTrace] = field(default_factory=list)


class Tool(Protocol):
    """Protocol for a tool usable by the decision agent."""

    def __call__(self, ctx: AgentContext, **kwargs: Any) -> dict[str, Any]:
        ...



