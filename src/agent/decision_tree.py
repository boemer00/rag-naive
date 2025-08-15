"""Intelligent decision-tree agent with semantic scoring, re-ranking, and query reformulation.

This module defines the `DecisionAgent` class that orchestrates retrieval, assessment, 
retries, and answer generation with a sophisticated self-healing loop featuring:
- Semantic similarity scoring using embeddings
- LLM-based result quality assessment
- Document re-ranking for improved relevance
- Intelligent query reformulation for failed retrievals
"""

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_chroma import Chroma

from .policy import PolicyConfig
from .tools import (
    assess_results,
    generate_answer,
    reformulate_query,
    retrieve_semantic,
    retrieve_with_filters,
)
from .types import AgentContext, AgentNodeTrace, AgentResult


@dataclass
class DecisionAgent:
    """Intelligent agent controller for multi-step RAG decisions with adaptive strategies.

    Uses a sophisticated three-pass approach:
    1. Semantic retrieval with re-ranking and LLM-based assessment
    2. Filtered retrieval with query augmentation (if Pass 1 fails)
    3. Query reformulation and retry (if Pass 2 fails)

    Parameters
    ----------
    index: Active Chroma index to use for retrieval.
    policy: Optional policy configuration controlling retry logic and thresholds.
    """

    index: Chroma
    policy: PolicyConfig = field(default_factory=PolicyConfig)

    def run(self, question: str) -> AgentResult:
        """Execute the intelligent decision-tree for a single question.

        Implements a three-pass strategy with increasing sophistication:
        1. Standard semantic retrieval with re-ranking
        2. Filtered retrieval with domain-specific query augmentation 
        3. LLM-powered query reformulation and final retry

        Each pass includes LLM-based quality assessment and stops when
        sufficient context is found or all strategies are exhausted.

        Returns
        -------
        AgentResult with answer, status ("completed"/"impossible"), and detailed trace.
        """

        ctx = AgentContext(question=question, config={
            "max_passes": self.policy.max_passes,
            "min_relevance_score": self.policy.min_relevance_score,
            "min_context_tokens": self.policy.min_context_tokens,
            "retrieval_k": 6,  # Default retrieval count
        })

        trace: list[AgentNodeTrace] = []

        # Pass 1: semantic retrieval
        semantic = retrieve_semantic(ctx, index=self.index, k=int(ctx.config.get("retrieval_k", 6)))
        trace.append(AgentNodeTrace(
            node_id="retrieve_semantic",
            name="retrieve_semantic",
            inputs={"k": ctx.config.get("retrieval_k", 6)},
            outputs={"score": semantic.get("score", 0.0), "num_docs": len(semantic.get("docs", []))},
            decision="retrieved",
        ))

        assess1 = assess_results(ctx, docs=semantic.get("docs", []))
        trace.append(AgentNodeTrace(
            node_id="assess_1",
            name="assess_results",
            inputs={"num_docs": len(semantic.get("docs", []))},
            outputs=assess1,
            decision="ok" if assess1["score"] >= ctx.config["min_relevance_score"] else "retry",
        ))

        if assess1["score"] >= ctx.config["min_relevance_score"]:
            answer = generate_answer(ctx, docs=semantic.get("docs", [])).get("answer")

            # Check for high confidence early termination
            confidence_level = "high" if assess1["score"] >= self.policy.high_confidence_threshold else "normal"

            trace.append(AgentNodeTrace(
                node_id="generate_answer_1",
                name="generate_answer",
                inputs={"source": "semantic", "confidence": confidence_level},
                outputs={
                    "has_answer": bool(answer),
                    "confidence_score": assess1["score"],
                    "context_length": len("\n\n".join(doc.page_content for doc in semantic.get("docs", [])))
                },
                decision="completed" if answer else "retry",
            ))
            if answer:
                return AgentResult(answer=answer, status="completed", trace=trace)

        # Pass 2: filtered retry (if enabled)
        if self.policy.enable_filtered_retry:
            filtered = retrieve_with_filters(ctx, index=self.index)
            trace.append(AgentNodeTrace(
                node_id="retrieve_filtered",
                name="retrieve_with_filters",
                inputs={"filters": filtered.get("filters", {})},
                outputs={"score": filtered.get("score", 0.0), "num_docs": len(filtered.get("docs", []))},
                decision="retrieved",
            ))
            assess2 = assess_results(ctx, docs=filtered.get("docs", []))
            trace.append(AgentNodeTrace(
                node_id="assess_2",
                name="assess_results",
                inputs={"num_docs": len(filtered.get("docs", []))},
                outputs=assess2,
                decision="ok" if assess2["score"] >= ctx.config["min_relevance_score"] else "retry",
            ))
            if assess2["score"] >= ctx.config["min_relevance_score"]:
                answer = generate_answer(ctx, docs=filtered.get("docs", [])).get("answer")

                # Enhanced trace for filtered retrieval
                confidence_level = "high" if assess2["score"] >= self.policy.high_confidence_threshold else "normal"

                trace.append(AgentNodeTrace(
                    node_id="generate_answer_2",
                    name="generate_answer",
                    inputs={
                        "source": "filtered",
                        "confidence": confidence_level,
                        "filters_applied": filtered.get("filters", {})
                    },
                    outputs={
                        "has_answer": bool(answer),
                        "confidence_score": assess2["score"],
                        "context_length": len("\n\n".join(doc.page_content for doc in filtered.get("docs", [])))
                    },
                    decision="completed" if answer else "retry",
                ))
                if answer:
                    return AgentResult(answer=answer, status="completed", trace=trace)

        # Pass 3: query reformulation and retry (if enabled)
        if self.policy.enable_semantic_retry:
            # Get previous failed context for reformulation
            failed_context = None
            if semantic.get("docs"):
                failed_context = "\n".join(doc.page_content[:200] for doc in semantic.get("docs", [])[:2])

            # Reformulate the query
            reformulated_question = reformulate_query(ctx.question, failed_context)
            trace.append(AgentNodeTrace(
                node_id="reformulate_query",
                name="reformulate_query",
                inputs={"original_question": ctx.question},
                outputs={"reformulated_question": reformulated_question},
                decision="reformulated",
            ))

            # Create new context with reformulated question
            reformulated_ctx = AgentContext(question=reformulated_question, config=ctx.config)

            # Retry with reformulated query
            retry_semantic = retrieve_semantic(reformulated_ctx, index=self.index, k=int(ctx.config.get("retrieval_k", 6)))
            trace.append(AgentNodeTrace(
                node_id="retrieve_reformulated",
                name="retrieve_semantic",
                inputs={"k": ctx.config.get("retrieval_k", 6), "reformulated": True},
                outputs={"score": retry_semantic.get("score", 0.0), "num_docs": len(retry_semantic.get("docs", []))},
                decision="retrieved",
            ))

            # Assess reformulated results (use original question for assessment)
            assess3 = assess_results(ctx, docs=retry_semantic.get("docs", []))
            trace.append(AgentNodeTrace(
                node_id="assess_reformulated",
                name="assess_results",
                inputs={"num_docs": len(retry_semantic.get("docs", []))},
                outputs=assess3,
                decision="ok" if assess3["score"] >= ctx.config["min_relevance_score"] else "impossible",
            ))

            if assess3["score"] >= ctx.config["min_relevance_score"]:
                # Generate answer using original question context for consistency
                answer = generate_answer(ctx, docs=retry_semantic.get("docs", [])).get("answer")

                # Final attempt - enhanced trace
                confidence_level = "high" if assess3["score"] >= self.policy.high_confidence_threshold else "normal"

                trace.append(AgentNodeTrace(
                    node_id="generate_answer_reformulated",
                    name="generate_answer",
                    inputs={
                        "source": "reformulated_query",
                        "confidence": confidence_level,
                        "original_question": ctx.question,
                        "reformulated_question": reformulated_question
                    },
                    outputs={
                        "has_answer": bool(answer),
                        "confidence_score": assess3["score"],
                        "context_length": len("\n\n".join(doc.page_content for doc in retry_semantic.get("docs", [])))
                    },
                    decision="completed" if answer else "impossible",
                ))
                if answer:
                    return AgentResult(answer=answer, status="completed", trace=trace)

        # If we reached here, we consider it impossible within policy limits
        return AgentResult(answer=None, status="impossible", trace=trace)
