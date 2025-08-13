"""Decision-tree agent scaffold (no implementation logic yet).

This module defines the `DecisionAgent` class that will orchestrate retrieval,
assessment, retries, and final answer generation with a self-healing loop and
an "impossible" stop state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_chroma import Chroma

from .policy import PolicyConfig
from .types import AgentContext, AgentNodeTrace, AgentResult


@dataclass
class DecisionAgent:
    """Agent controller for multi-step RAG decisions (scaffold).

    Parameters
    ----------
    index: Active Chroma index to use for retrieval.
    policy: Optional policy configuration; sensible defaults are provided.
    """

    index: Chroma
    policy: PolicyConfig = PolicyConfig()

    def run(self, question: str) -> AgentResult:
        """Execute the decision-tree for a single question.

        Notes
        -----
        - This scaffold returns a placeholder result. Implementation will be
          provided in a later step.
        """

        ctx = AgentContext(question=question, config={
            "max_passes": self.policy.max_passes,
            "min_relevance_score": self.policy.min_relevance_score,
            "min_context_tokens": self.policy.min_context_tokens,
        })

        trace: list[AgentNodeTrace] = []

        # Placeholder minimal trace entry to validate wiring in tests later
        trace.append(AgentNodeTrace(
            node_id="start",
            name="start",
            inputs={"question": question},
            outputs={},
            decision="noop",
        ))

        return AgentResult(answer=None, status="max_passes", trace=trace)


