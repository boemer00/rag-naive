"""
Unit tests for PMC source functionality.
Tests individual components in isolation.
"""

from src.sources.paper_tracker import PaperTracker
from src.sources.pmc import PMCSource


class TestPMCSource:
    """Unit tests for PMC source."""

    def test_longevity_keyword_filtering(self):
        """Test that longevity keywords are properly defined."""
        pmc = PMCSource()
        assert 'longevity' in pmc.longevity_keywords
        assert 'aging' in pmc.longevity_keywords
        assert 'healthspan' in pmc.longevity_keywords
        assert len(pmc.longevity_keywords) >= 8

    def test_filter_longevity_papers(self):
        """Test longevity paper filtering logic."""
        pmc = PMCSource()

        # Mock papers with different relevance
        papers = [
            {'title': 'Longevity and aging in mice', 'abstract': 'Study on aging mechanisms'},
            {'title': 'Cancer treatment protocols', 'abstract': 'Oncology research'},
            {'title': 'Healthspan extension', 'abstract': 'Lifespan and mortality studies'}
        ]

        filtered = pmc._filter_longevity_papers(papers)

        # Should filter to only longevity-relevant papers
        assert len(filtered) == 2
        assert all('longevity_score' in paper for paper in filtered)
        assert filtered[0]['longevity_score'] >= filtered[1]['longevity_score']

    def test_author_field_handling(self):
        """Test handling of different author field formats."""
        pmc = PMCSource()

        # Test dict format authors
        paper_dict_authors = {
            'title': 'Test Paper',
            'authors': [{'name': 'Smith J', 'authtype': 'Author'}, {'name': 'Doe A', 'authtype': 'Author'}],
            'abstract': 'Test about longevity'
        }

        doc = pmc._create_document(paper_dict_authors, "Test content")
        assert doc.metadata['authors'] == 'Smith J, Doe A'

        # Test string format authors
        paper_str_authors = {
            'title': 'Test Paper',
            'authors': ['Smith J', 'Doe A'],
            'abstract': 'Test about aging'
        }

        doc = pmc._create_document(paper_str_authors, "Test content")
        assert doc.metadata['authors'] == 'Smith J, Doe A'


class TestPaperTracker:
    """Unit tests for paper tracking functionality."""

    def test_database_initialization(self, isolated_test_env):
        """Test that database initializes correctly."""
        tracker = PaperTracker(isolated_test_env)
        stats = tracker.get_stats()

        assert stats['total_papers'] == 0
        assert stats['processed_papers'] == 0

    def test_add_and_retrieve_paper(self, isolated_test_env):
        """Test adding and retrieving paper metadata."""
        tracker = PaperTracker(isolated_test_env)

        paper_data = {
            'paper_id': 'PMC123456',
            'title': 'Test Longevity Paper',
            'authors': ['Smith J', 'Doe A'],
            'abstract': 'Test abstract about aging',
            'journal': 'Test Journal',
            'pub_date': '2023-01-01',
            'source_type': 'pmc',
            'pmc_id': 'PMC123456',
            'processed': False
        }

        # Add paper
        success = tracker.add_paper(paper_data)
        assert success

        # Check if stored
        assert tracker.is_paper_stored('PMC123456')
        assert 'PMC123456' in tracker.get_stored_ids()

        # Check stats
        stats = tracker.get_stats()
        assert stats['total_papers'] == 1
        assert stats['pmc_papers'] == 1
