"""Policy configuration for the intelligent decision-tree agent."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PolicyConfig:
    """Parameters controlling the agent's adaptive retrieval and decision strategies.
    Attributes
    ----------
    max_passes : int
        Maximum number of retrieval attempts (default: 3)
    min_relevance_score : float
        Minimum relevance threshold for accepting results (0.0-1.0, default: 0.5)
    min_context_tokens : int
        Minimum context length required for answer generation (default: 300)
    enable_filtered_retry : bool
        Whether to attempt filtered retrieval on Pass 2 (default: True)
    enable_semantic_retry : bool
        Whether to attempt query reformulation on Pass 3 (default: True)
    high_confidence_threshold : float
        Score threshold for early termination with high confidence (default: 0.8)
    """

    max_passes: int = 3
    min_relevance_score: float = 0.5
    min_context_tokens: int = 300
    enable_filtered_retry: bool = True
    enable_semantic_retry: bool = True
    high_confidence_threshold: float = 0.8
