"""
Unit tests for RAG prompt contract.
Ensures longevity persona, section structure, and no chain-of-thought exposure.
"""

from src.chain import PROMPT_RAG


def test_prompt_persona_mentions_longevity():
    text = PROMPT_RAG.lower()
    assert "longevity" in text
    assert any(term in text for term in ["aging", "healthspan"])  # at least one


def test_prompt_has_required_sections():
    text = PROMPT_RAG
    assert "**Answer**" in text
    assert "**Details**" in text
    assert "**Citations**" in text
    assert "**Limitations**" in text


def test_prompt_disallows_chain_of_thought():
    text = PROMPT_RAG.lower()
    assert "chain-of-thought" not in text
    # Also ensure we instruct to avoid revealing reasoning
    assert "do not reveal internal reasoning" in text


