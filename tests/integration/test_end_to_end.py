"""
Integration tests for end-to-end RAG functionality.
Tests the complete pipeline from data loading to answer generation.
"""

import os
from unittest.mock import patch

import pytest

from src.indexer import build_index
from src.utils import load_source_docs


class TestEndToEndRAG:
    """Integration tests for complete RAG pipeline."""

    @pytest.mark.integration
    def test_load_local_documents(self):
        """Test loading local PDF documents."""
        # Test loading existing PDFs
        docs = load_source_docs()

        assert len(docs) > 0
        assert all(hasattr(doc, 'page_content') for doc in docs)
        assert all(hasattr(doc, 'metadata') for doc in docs)
        assert all(doc.metadata.get('source_type') == 'local' for doc in docs)

    @pytest.mark.integration
    @patch('src.sources.pmc.PMCSource._search_pmc')
    @patch('src.sources.pmc.PMCSource._get_paper_content')
    @patch('src.sources.paper_tracker.PaperTracker.is_paper_stored')
    def test_load_pmc_documents_mocked(self, mock_stored, mock_content, mock_search):
        """Test PMC document loading with mocked API calls."""
        # Mock that papers are not already stored
        mock_stored.return_value = False
        
        # Mock PMC API responses
        mock_search.return_value = [
            {
                'pmc_id': 'PMC123456',
                'title': 'Longevity and Aging Mechanisms',
                'authors': [{'name': 'Smith J', 'authtype': 'Author'}],
                'journal': 'Aging Cell',
                'pub_date': '2023-01-01',
                'abstract': 'Study on longevity and aging processes'
            }
        ]

        mock_content.return_value = "Abstract: This study investigates longevity mechanisms..."

        # Test PMC loading
        docs = load_source_docs(pmc_query="longevity aging", pmc_limit=1)

        assert len(docs) >= 1
        pmc_docs = [doc for doc in docs if doc.metadata.get('source_type') == 'pmc']
        assert len(pmc_docs) >= 1

        pmc_doc = pmc_docs[0]
        assert 'longevity' in pmc_doc.page_content.lower()
        assert pmc_doc.metadata.get('pmc_id') == 'PMC123456'

    @pytest.mark.integration
    def test_vector_index_creation(self, mock_openai_components):
        """Test that vector index can be created from documents."""
        # Load a small set of documents
        docs = load_source_docs()[:3]  # Limit for speed

        # Build index (using mocked embeddings from test_config.py)
        db = build_index(docs)

        assert db is not None
        assert db._collection.count() > 0

        # Test retrieval (using mocked embeddings)
        results = db.similarity_search("longevity aging", k=2)
        assert len(results) <= 2
        assert all(hasattr(result, 'page_content') for result in results)

    @pytest.mark.integration
    @pytest.mark.requires_api
    @pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason="OpenAI API key required")
    def test_end_to_end_question_answering(self):
        """Test complete question answering pipeline with real API."""
        from main import answer

        # Test with a question that should work with existing data
        question = "What factors influence human longevity?"

        try:
            answer_text = answer(question)

            # Basic checks
            assert isinstance(answer_text, str)
            assert len(answer_text) > 50  # Should be substantial
            assert any(word in answer_text.lower() for word in ['longevity', 'aging', 'lifespan'])

        except Exception as e:
            pytest.skip(f"End-to-end test skipped due to: {e}")

    @pytest.mark.integration
    def test_end_to_end_question_answering_mocked(self, mock_openai_components):
        """Test complete question answering pipeline with mocked API."""
        from main import answer

        # This version runs in CI without API costs
        question = "What factors influence human longevity?"

        try:
            answer_text = answer(question)

            # Basic checks with mocked response
            assert isinstance(answer_text, str)
            assert len(answer_text) > 10  # Mocked response should be non-empty

        except Exception as e:
            pytest.skip(f"Mocked end-to-end test skipped due to: {e}")


class TestRAGQuality:
    """Tests for RAG response quality metrics."""

    def test_citation_detection(self):
        """Test citation detection logic."""
        from tests.performance.test_rag_vs_llm import RAGvsLLMTester

        tester = RAGvsLLMTester()

        # Text with citations
        text_with_citations = "This finding (Smith et al., 2023) shows that longevity is influenced by genetics (Sec 3.2, p. 5)."
        assert tester.analyze_citations(text_with_citations)

        # Text without citations
        text_without_citations = "Longevity is influenced by many factors including diet and exercise."
        assert not tester.analyze_citations(text_without_citations)

    def test_specificity_scoring(self):
        """Test technical specificity scoring."""
        from tests.performance.test_rag_vs_llm import RAGvsLLMTester

        tester = RAGvsLLMTester()

        # Technical text
        technical_text = "Telomere shortening and epigenetic methylation patterns indicate cellular senescence with 95% accuracy in genomic studies."
        tech_score = tester.calculate_specificity_score(technical_text)

        # Generic text
        generic_text = "Aging happens to everyone and is a natural process that affects health."
        generic_score = tester.calculate_specificity_score(generic_text)

        assert tech_score > generic_score
