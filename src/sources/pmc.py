import time
import xml.etree.ElementTree as ET

import requests
from langchain.schema import Document

from .base import ResearchSource
from .paper_tracker import PaperTracker


class PMCSource(ResearchSource):
    """PMC (PubMed Central) research paper source with longevity focus."""

    def __init__(self, db_path: str = "papers.db", rate_limit: float = 0.34):
        self.tracker = PaperTracker(db_path)
        self.rate_limit = rate_limit  # 3 requests per second = 0.33s between requests
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

        # Longevity-focused keywords for filtering
        self.longevity_keywords = [
            'longevity', 'aging', 'ageing', 'lifespan', 'healthspan',
            'life expectancy', 'mortality', 'cellular senescence',
            'anti-aging', 'age-related', 'geriatric', 'gerontology'
        ]

    def fetch_papers(self, query: str, limit: int = 100) -> list[Document]:
        """Fetch longevity papers from PMC, filtered by relevance."""
        print(f"Fetching {limit} longevity papers from PMC...")

        # Search PMC for relevant papers
        search_results = self._search_pmc(query, limit * 2)  # Get more to allow filtering

        # Filter for longevity relevance
        longevity_papers = self._filter_longevity_papers(search_results)

        # Limit to requested number
        top_papers = longevity_papers[:limit]

        documents = []
        for i, paper in enumerate(top_papers):
            print(f"Processing paper {i+1}/{len(top_papers)}: {paper.get('title', 'Unknown')[:60]}...")

            # Skip if already stored
            paper_id = paper.get('pmc_id', paper.get('pmid'))
            if self.is_paper_stored(paper_id):
                print("  Skipping - already stored")
                continue

            # Get full text content
            content = self._get_paper_content(paper)
            if content:
                # Store in tracker
                self._store_paper_metadata(paper, content)

                # Create document for vector DB
                doc = self._create_document(paper, content)
                if doc:
                    documents.append(doc)

            # Rate limiting
            time.sleep(self.rate_limit)

        print(f"Successfully processed {len(documents)} new papers")
        return documents

    def _search_pmc(self, query: str, limit: int) -> list[dict]:
        """Search PMC for papers matching query."""
        search_url = f"{self.base_url}/esearch.fcgi"
        params = {
            'db': 'pmc',
            'term': f"{query} AND open access[filter]",  # Only open access papers
            'retmax': limit,
            'retmode': 'json',
            'sort': 'relevance'  # Sort by relevance as requested
        }

        try:
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            pmc_ids = data.get('esearchresult', {}).get('idlist', [])
            print(f"Found {len(pmc_ids)} PMC papers")

            # Get detailed info for each paper
            return self._get_paper_details(pmc_ids)

        except Exception as e:
            print(f"Error searching PMC: {e}")
            return []

    def _get_paper_details(self, pmc_ids: list[str]) -> list[dict]:
        """Get detailed metadata for PMC papers."""
        if not pmc_ids:
            return []

        summary_url = f"{self.base_url}/esummary.fcgi"
        params = {
            'db': 'pmc',
            'id': ','.join(pmc_ids),
            'retmode': 'json'
        }

        try:
            response = requests.get(summary_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            papers = []
            for pmc_id, paper_data in data.get('result', {}).items():
                if pmc_id in ['uids']:  # Skip metadata entries
                    continue

                papers.append({
                    'pmc_id': f"PMC{pmc_id}",
                    'pmid': paper_data.get('pmid'),
                    'title': paper_data.get('title', ''),
                    'authors': paper_data.get('authors', []),
                    'journal': paper_data.get('fulljournalname', ''),
                    'pub_date': paper_data.get('pubdate', ''),
                    'doi': paper_data.get('doi', ''),
                    'abstract': ''  # Will be filled by content fetching
                })

            return papers

        except Exception as e:
            print(f"Error getting paper details: {e}")
            return []

    def _filter_longevity_papers(self, papers: list[dict]) -> list[dict]:
        """Filter papers for longevity relevance based on title/abstract keywords."""
        longevity_papers = []

        for paper in papers:
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', '').lower()
            text_to_check = f"{title} {abstract}"

            # Check if any longevity keywords are present
            relevance_score = sum(1 for keyword in self.longevity_keywords
                                if keyword in text_to_check)

            if relevance_score > 0:
                paper['longevity_score'] = relevance_score
                longevity_papers.append(paper)

        # Sort by relevance score (descending)
        longevity_papers.sort(key=lambda x: x.get('longevity_score', 0), reverse=True)
        print(f"Filtered to {len(longevity_papers)} longevity-relevant papers")

        return longevity_papers

    def _get_paper_content(self, paper: dict) -> str | None:
        """Get full text content from PMC."""
        pmc_id = paper.get('pmc_id', '').replace('PMC', '')
        if not pmc_id:
            return None

        fetch_url = f"{self.base_url}/efetch.fcgi"
        params = {
            'db': 'pmc',
            'id': pmc_id,
            'retmode': 'xml'
        }

        try:
            response = requests.get(fetch_url, params=params, timeout=20)
            response.raise_for_status()

            # Parse XML and extract text content
            root = ET.fromstring(response.content)

            # Extract sections
            sections = []

            # Abstract
            abstract = self._extract_section(root, './/abstract')
            if abstract:
                sections.append(f"Abstract: {abstract}")
                paper['abstract'] = abstract  # Store for filtering

            # Introduction
            intro = self._extract_section(root, './/sec[@sec-type="intro"]') or \
                   self._extract_section(root, './/sec[title[contains(text(), "Introduction")]]')
            if intro:
                sections.append(f"Introduction: {intro}")

            # Methods
            methods = self._extract_section(root, './/sec[@sec-type="methods"]') or \
                     self._extract_section(root, './/sec[title[contains(text(), "Method")]]')
            if methods:
                sections.append(f"Methods: {methods}")

            # Results
            results = self._extract_section(root, './/sec[@sec-type="results"]') or \
                     self._extract_section(root, './/sec[title[contains(text(), "Result")]]')
            if results:
                sections.append(f"Results: {results}")

            # Discussion/Conclusion
            discussion = self._extract_section(root, './/sec[@sec-type="discussion"]') or \
                        self._extract_section(root, './/sec[title[contains(text(), "Discussion")]]') or \
                        self._extract_section(root, './/sec[title[contains(text(), "Conclusion")]]')
            if discussion:
                sections.append(f"Discussion: {discussion}")

            return '\n\n'.join(sections) if sections else None

        except Exception as e:
            print(f"  Error fetching content for {paper.get('title', 'Unknown')}: {e}")
            return None

    def _extract_section(self, root, xpath: str) -> str | None:
        """Extract text content from XML section."""
        try:
            elements = root.findall(xpath)
            if not elements:
                return None

            texts = []
            for elem in elements:
                # Get all text content, excluding references
                text_parts = []
                for text_elem in elem.iter():
                    if text_elem.tag in ['xref', 'ref']:  # Skip references
                        continue
                    if text_elem.text:
                        text_parts.append(text_elem.text.strip())
                    if text_elem.tail:
                        text_parts.append(text_elem.tail.strip())

                section_text = ' '.join(text_parts).strip()
                if section_text:
                    texts.append(section_text)

            return ' '.join(texts) if texts else None

        except Exception:
            return None

    def _store_paper_metadata(self, paper: dict, content: str):
        """Store paper metadata in SQLite tracker."""
        # Handle authors field - can be list of dicts or strings
        authors_list = paper.get('authors', [])
        if authors_list and isinstance(authors_list[0], dict):
            authors_for_storage = [author.get('name', '') for author in authors_list]
        else:
            authors_for_storage = authors_list if authors_list else []

        paper_data = {
            'paper_id': paper.get('pmc_id', paper.get('pmid')),
            'title': paper.get('title', ''),
            'authors': authors_for_storage,
            'abstract': paper.get('abstract', ''),
            'journal': paper.get('journal', ''),
            'pub_date': paper.get('pub_date', ''),
            'source_type': 'pmc',
            'pmc_id': paper.get('pmc_id'),
            'pmid': paper.get('pmid'),
            'doi': paper.get('doi'),
            'keywords': self.longevity_keywords,  # Store filtering keywords used
            'processed': False
        }
        self.tracker.add_paper(paper_data)

    def _create_document(self, paper: dict, content: str) -> Document | None:
        """Create LangChain Document from paper content."""
        if not content:
            return None

        # Handle authors field - can be list of dicts or strings
        authors_list = paper.get('authors', [])
        if authors_list and isinstance(authors_list[0], dict):
            authors_str = ', '.join([author.get('name', '') for author in authors_list])
        else:
            authors_str = ', '.join(authors_list) if authors_list else ''

        metadata = {
            'paper_id': paper.get('pmc_id', paper.get('pmid')),
            'title': paper.get('title', ''),
            'authors': authors_str,
            'journal': paper.get('journal', ''),
            'pub_date': paper.get('pub_date', ''),
            'source_type': 'pmc',
            'pmc_id': paper.get('pmc_id'),
            'pmid': paper.get('pmid'),
            'doi': paper.get('doi'),
            'paper_title': paper.get('title', ''),  # For compatibility with existing system
            'source_file': f"{paper.get('pmc_id', 'unknown')}.xml",
            'longevity_score': paper.get('longevity_score', 0)
        }

        return Document(page_content=content, metadata=metadata)

    def get_stored_ids(self) -> set[str]:
        """Get IDs of papers already stored."""
        return self.tracker.get_stored_ids('pmc')

    def is_paper_stored(self, paper_id: str) -> bool:
        """Check if paper is already stored."""
        return self.tracker.is_paper_stored(paper_id)

    def get_stats(self) -> dict:
        """Get PMC source statistics."""
        return self.tracker.get_stats()
