"""Agent package scaffolding for decision-tree orchestration.

This package defines public interfaces for an agentic decision-tree that
coordinates retrieval, assessment, and answer generation. Implementations will
be added in a later step.
"""

from .decision_tree import DecisionAgent
from .policy import PolicyConfig
from .types import AgentContext, AgentNodeTrace, AgentResult, StopReason

__all__ = [
    "AgentContext",
    "AgentNodeTrace",
    "AgentResult",
    "StopReason",
    "PolicyConfig",
    "DecisionAgent",
]


