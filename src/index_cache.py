
from langchain_chroma import Chroma

from src.indexer import load_index


class IndexCache:
    """Simple in-memory cache for vector index to avoid repeated loading."""

    def __init__(self):
        self._index: Chroma | None = None

    def get_index(self) -> Chroma:
        """Get cached index or load from disk if not cached."""
        if self._index is None:
            self._index = load_index()
        return self._index

    def clear_cache(self) -> None:
        """Clear cached index (useful when index is rebuilt)."""
        self._index = None


# Global index cache instance
_index_cache: IndexCache | None = None

def get_index_cache() -> IndexCache:
    """Get global index cache instance."""
    global _index_cache
    if _index_cache is None:
        _index_cache = IndexCache()
    return _index_cache
