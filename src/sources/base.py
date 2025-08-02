from abc import ABC, abstractmethod
from typing import List, Set
from langchain.schema import Document


class ResearchSource(ABC):
    """Abstract base class for research paper sources."""
    
    @abstractmethod
    def fetch_papers(self, query: str, limit: int = 100) -> List[Document]:
        """Fetch papers matching the query."""
        pass
    
    @abstractmethod
    def get_stored_ids(self) -> Set[str]:
        """Get IDs of papers already stored."""
        pass
    
    @abstractmethod
    def is_paper_stored(self, paper_id: str) -> bool:
        """Check if paper is already stored."""
        pass