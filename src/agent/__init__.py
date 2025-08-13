"""Agent package scaffolding for decision-tree orchestration.

This package defines public interfaces for an agentic decision-tree that
coordinates retrieval, assessment, and answer generation. Implementations will
be added in a later step.
"""

from .types import (
    AgentContext,
    AgentNodeTrace,
    AgentResult,
    StopReason,
)

from .policy import PolicyConfig
from .decision_tree import DecisionAgent

__all__ = [
    "AgentContext",
    "AgentNodeTrace",
    "AgentResult",
    "StopReason",
    "PolicyConfig",
    "DecisionAgent",
]


