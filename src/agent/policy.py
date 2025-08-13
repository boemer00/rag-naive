"""Policy configuration for the decision-tree agent (scaffold only)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PolicyConfig:
    """Parameters controlling the agent's self-healing loop and decisions."""

    max_passes: int = 3
    min_relevance_score: float = 0.5
    min_context_tokens: int = 300
    enable_filtered_retry: bool = True
    enable_semantic_retry: bool = True


