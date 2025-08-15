"""Intelligent tools for the decision-tree agent with semantic scoring and LLM-based assessment.

Each tool follows the protocol defined in `src.agent.types.Tool` and returns a
generic result payload with sophisticated evaluation capabilities.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

from config import get_config
from src.chain import PROMPT_RAG

from .types import AgentContext


def _infer_filters_from_question(question: str) -> dict[str, Any]:
    """Infer simple metadata filters from the user's question.

    This implementation keeps to exact-match filters that work reliably with
    Chroma's metadata filtering. Topic/biomarker signals are appended to the
    query string by the caller rather than used as strict filters since those
    fields are stored as comma-separated strings in the current index.
    """

    q = question.lower()
    study_type: str | None = None

    if any(w in q for w in ["meta-analysis", "systematic review"]):
        study_type = "meta-analysis"
    elif any(w in q for w in ["randomized", "rct", "clinical trial"]):
        study_type = "rct"
    elif any(w in q for w in ["cohort", "observational", "longitudinal"]):
        study_type = "observational"

    filters: dict[str, Any] = {}
    if study_type:
        filters["study_type"] = study_type

    return filters


def _score_docs_semantic(question: str, docs: list[Document]) -> float:
    """Semantic scoring using embedding similarity.
    Uses cosine similarity between question embedding and document embeddings
    to provide more accurate relevance assessment.
    Returns score in [0, 1].
    """
    if not docs:
        return 0.0

    try:
        config = get_config()
        embeddings = OpenAIEmbeddings(
            model=config.embedding_model,
            openai_api_key=config.openai_api_key
        )

        # Get question embedding
        question_embedding = embeddings.embed_query(question)

        # Get document embeddings (sample first 1000 chars for efficiency)
        doc_texts = [doc.page_content[:1000] for doc in docs]
        doc_embeddings = embeddings.embed_documents(doc_texts)

        # Calculate cosine similarities
        question_emb = np.array(question_embedding).reshape(1, -1)
        doc_embs = np.array(doc_embeddings)

        similarities = cosine_similarity(question_emb, doc_embs)[0]

        # Combine top similarities with document count factor
        avg_similarity = np.mean(similarities)
        max_similarity = np.max(similarities)
        count_factor = min(1.0, len(docs) / 6.0)

        # Weighted combination
        semantic_score = 0.6 * max_similarity + 0.3 * avg_similarity + 0.1 * count_factor

        return max(0.0, min(1.0, semantic_score))

    except Exception:
        # Fallback to basic scoring if embeddings fail
        return _score_docs_fallback(question, docs)


def _score_docs_fallback(question: str, docs: list[Document]) -> float:
    """Fallback heuristic scoring when embeddings are unavailable."""
    if not docs:
        return 0.0

    q = question.lower()
    length_score = min(1.0, sum(len(d.page_content) for d in docs) / 4000.0)

    # Basic keyword overlap
    keywords = [
        w for w in q.replace("?", " ").replace(",", " ").split() if len(w) > 3
    ][:8]
    if not keywords:
        overlap_score = 0.3
    else:
        hits = 0
        sample_text = "\n".join(d.page_content for d in docs)[:4000].lower()
        for w in keywords:
            if w in sample_text:
                hits += 1
        overlap_score = min(1.0, hits / max(1, len(keywords)))

    count_score = min(1.0, len(docs) / 6.0)
    return max(0.0, min(1.0, 0.4 * length_score + 0.4 * overlap_score + 0.2 * count_score))


def retrieve_semantic(ctx: AgentContext, *, index: Chroma, k: int | None = None) -> dict[str, Any]:
    """Semantic retrieval with re-ranking for improved relevance.

    Returns: {"docs": list[Document], "score": float}
    """

    if k is None:
        k = int(ctx.config.get("retrieval_k", 6))

    # Retrieve more documents initially to improve re-ranking
    retrieval_k = min(k * 2, 12)  # Retrieve 2x desired, max 12
    retriever = index.as_retriever(search_type="similarity", search_kwargs={"k": retrieval_k})
    initial_docs: list[Document] = retriever.invoke(ctx.question)

    # Re-rank and select top k
    reranked_docs = rerank_documents(ctx.question, initial_docs, top_k=k)

    score = _score_docs_semantic(ctx.question, reranked_docs)
    return {"docs": reranked_docs, "score": score}


def retrieve_with_filters(ctx: AgentContext, *, index: Chroma, filters: dict[str, Any] | None = None, k: int | None = None) -> dict[str, Any]:
    """Filtered retrieval with query augmentation and re-ranking.

    Returns: {"docs": list[Document], "score": float, "filters": dict}
    """

    if k is None:
        k = int(ctx.config.get("retrieval_k", 6))

    effective_filters = filters or _infer_filters_from_question(ctx.question)

    # Augment the question with likely topic/biomarker hints for better recall
    q = ctx.question
    lower = q.lower()
    augment_terms: list[str] = []
    topic_map = {
        "cardiovascular": ["cardiovascular", "heart", "blood pressure"],
        "sleep": ["sleep", "circadian"],
        "exercise": ["exercise", "training", "fitness"],
        "nutrition": ["nutrition", "diet", "caloric"],
        "longevity": ["longevity", "aging", "lifespan"],
    }
    biomarkers = {"vo2_max": ["vo2", "oxygen consumption"], "heart_rate": ["resting heart"], "blood_pressure": ["blood pressure"], "sleep_metrics": ["sleep"]}

    for key, words in {**topic_map, **biomarkers}.items():
        if any(w in lower for w in words):
            augment_terms.append(key)

    augmented_query = q if not augment_terms else f"{q} {' '.join(set(augment_terms))}"

    # Retrieve more documents for better re-ranking
    retrieval_k = min(k * 2, 12)  # Retrieve 2x desired, max 12
    initial_docs: list[Document] = index.similarity_search(augmented_query, k=retrieval_k, filter=effective_filters or None)

    # Re-rank based on original question (not augmented)
    reranked_docs = rerank_documents(ctx.question, initial_docs, top_k=k)

    score = _score_docs_semantic(ctx.question, reranked_docs)
    return {"docs": reranked_docs, "score": score, "filters": effective_filters}


def assess_results(ctx: AgentContext, *, docs: list[Any]) -> dict[str, Any]:
    """LLM-based assessment of retrieval results quality.
    Uses both semantic similarity scoring and LLM evaluation to determine
    if the retrieved context is sufficient to answer the question.
    """
    if not docs:
        return {"score": 0.0, "reason": "no documents retrieved"}

    # Get semantic similarity score
    semantic_score = _score_docs_semantic(ctx.question, docs)

    # If semantic score is very low, don't bother with LLM assessment
    if semantic_score < 0.2:
        return {"score": semantic_score, "reason": "low semantic relevance"}

    # LLM-based assessment for borderline cases
    try:
        llm_score, llm_reason = _assess_with_llm(ctx.question, docs)

        # Combine semantic and LLM scores
        final_score = 0.6 * semantic_score + 0.4 * llm_score

        return {
            "score": final_score,
            "reason": llm_reason,
            "semantic_score": semantic_score,
            "llm_score": llm_score
        }

    except Exception:
        # Fallback to semantic score only
        reason = "insufficient context" if semantic_score < float(ctx.config.get("min_relevance_score", 0.5)) else "sufficient context"
        return {"score": semantic_score, "reason": reason}


def rerank_documents(question: str, docs: list[Document], top_k: int | None = None) -> list[Document]:
    """Re-rank documents using embedding similarity for better relevance.
    Uses cosine similarity between question and document embeddings to
    re-order documents by relevance, keeping only top_k if specified.
    """
    if not docs:
        return docs

    if len(docs) <= 1:
        return docs

    if top_k is None:
        top_k = len(docs)

    try:
        config = get_config()
        embeddings = OpenAIEmbeddings(
            model=config.embedding_model,
            openai_api_key=config.openai_api_key
        )

        # Get question embedding
        question_embedding = embeddings.embed_query(question)

        # Get document embeddings (use more text for re-ranking)
        doc_texts = [doc.page_content[:1500] for doc in docs]
        doc_embeddings = embeddings.embed_documents(doc_texts)

        # Calculate similarities
        question_emb = np.array(question_embedding).reshape(1, -1)
        doc_embs = np.array(doc_embeddings)

        similarities = cosine_similarity(question_emb, doc_embs)[0]

        # Create (similarity, doc) pairs and sort by similarity desc
        doc_scores = list(zip(similarities, docs, strict=False))
        doc_scores.sort(key=lambda x: x[0], reverse=True)

        # Return top_k documents
        return [doc for _, doc in doc_scores[:top_k]]

    except Exception:
        # If re-ranking fails, return original documents
        return docs[:top_k] if top_k < len(docs) else docs


def reformulate_query(original_question: str, failed_context: str | None = None) -> str:
    """Use LLM to reformulate a query for better retrieval results.
    Analyzes why the original query may have failed and creates an improved version
    with better keywords, synonyms, or alternative framing.
    """
    config = get_config()

    # Create reformulation prompt
    reformulation_prompt = PromptTemplate(
        input_variables=["question", "failed_context"],
        template="""You are helping improve a search query for a longevity research database.

Original Question: {question}

{failed_context}

Your task is to reformulate this question to get better search results. Consider:
1. Adding relevant scientific/medical synonyms
2. Including related biomarkers or mechanisms
3. Using more specific terminology
4. Breaking complex questions into key concepts

Focus on longevity research topics like: aging, cardiovascular health, VO2 max, HRV, sleep quality, exercise, nutrition, biomarkers.

Respond with ONLY the reformulated question, no explanation.

Reformulated Question:"""
    )

    # Determine context based on failed retrieval
    if failed_context:
        context_info = f"Previous search found limited relevant information:\n{failed_context[:500]}\n"
    else:
        context_info = "Previous search returned no relevant results.\n"

    llm = ChatOpenAI(
        model=config.model_name,
        temperature=0.3,  # Some creativity but consistent
        max_tokens=100,
        openai_api_key=config.openai_api_key
    )

    try:
        formatted = reformulation_prompt.format(
            question=original_question,
            failed_context=context_info
        )
        response = llm.invoke(formatted)
        reformulated = response.content.strip()

        # Return reformulated question if it looks valid, otherwise original
        if reformulated and len(reformulated) > 10 and reformulated != original_question:
            return reformulated
        else:
            return _create_fallback_reformulation(original_question)

    except Exception:
        return _create_fallback_reformulation(original_question)


def _create_fallback_reformulation(question: str) -> str:
    """Create a simple reformulated query using keyword expansion."""
    q_lower = question.lower()

    # Find relevant terms to add
    relevant_terms = []
    if any(word in q_lower for word in ["heart", "cardio", "blood pressure"]):
        relevant_terms.extend(["cardiovascular", "cardiac"])
    if any(word in q_lower for word in ["sleep", "rest"]):
        relevant_terms.extend(["sleep quality", "circadian"])
    if any(word in q_lower for word in ["exercise", "fitness", "training"]):
        relevant_terms.extend(["physical activity", "aerobic"])
    if any(word in q_lower for word in ["vo2", "oxygen"]):
        relevant_terms.extend(["cardiorespiratory fitness", "aerobic capacity"])

    # Add general longevity terms if none found
    if not relevant_terms:
        relevant_terms = ["aging", "longevity"]

    # Return augmented question
    return f"{question} {' '.join(relevant_terms[:2])}"


def _assess_with_llm(question: str, docs: list[Document]) -> tuple[float, str]:
    """Use LLM to assess if retrieved context can answer the question."""
    config = get_config()

    # Sample context to avoid token limits
    context = "\n\n".join(doc.page_content for doc in docs[:3])[:2000]

    assessment_prompt = PromptTemplate(
        input_variables=["question", "context"],
        template="""You are evaluating whether the provided context contains sufficient information to answer the given question.

Question: {question}

Context:
{context}

Evaluate on a scale of 0.0 to 1.0 how well this context can answer the question:
- 1.0: Perfect, comprehensive answer possible
- 0.7-0.9: Good, can answer most aspects
- 0.4-0.6: Partial, some relevant information
- 0.0-0.3: Insufficient, little to no relevant information

Respond with ONLY a number between 0.0 and 1.0, followed by a brief reason (max 10 words).
Format: SCORE|REASON

Example: 0.8|Contains relevant data on cardiovascular effects"""
    )

    llm = ChatOpenAI(
        model=config.model_name,
        temperature=0.1,  # Low temperature for consistent assessment
        max_tokens=50,
        openai_api_key=config.openai_api_key
    )

    formatted = assessment_prompt.format(question=question, context=context)
    response = llm.invoke(formatted)
    result = response.content.strip()

    try:
        parts = result.split('|')
        score = float(parts[0])
        reason = parts[1] if len(parts) > 1 else "LLM assessment"
        return max(0.0, min(1.0, score)), reason
    except (ValueError, IndexError):
        # Parse failed, return neutral score
        return 0.5, "assessment parse error"


def generate_answer(ctx: AgentContext, *, docs: list[Any]) -> dict[str, Any]:
    """Generate a final answer from selected docs using PROMPT_RAG and ChatOpenAI."""

    if not docs:
        return {"answer": None}

    config = get_config()
    context_text = "\n\n".join(d.page_content for d in docs)

    prompt = PromptTemplate(input_variables=["context", "question"], template=PROMPT_RAG)
    formatted = prompt.format(context=context_text, question=ctx.question)

    llm = ChatOpenAI(
        model=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        openai_api_key=config.openai_api_key,
    )
    response = llm.invoke(formatted)
    answer = response.content if hasattr(response, "content") else str(response)
    return {
        "answer": answer,
        "context_length": len(context_text),
        "doc_count": len(docs)
    }
