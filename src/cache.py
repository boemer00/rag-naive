import hashlib
import pickle
from pathlib import Path
from typing import Any, Optional

from config import get_config


class SimpleCache:
    """Simple file-based cache for RAG responses."""
    
    def __init__(self):
        config = get_config()
        self.cache_dir = Path(config.persist_directory) / "cache"
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_key(self, question: str) -> str:
        """Generate cache key from question."""
        return hashlib.md5(question.lower().strip().encode()).hexdigest()
    
    def get(self, question: str) -> Optional[str]:
        """Get cached response for question."""
        key = self._get_key(question)
        cache_file = self.cache_dir / f"{key}.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                pass
        return None
    
    def set(self, question: str, answer: str) -> None:
        """Cache response for question."""
        key = self._get_key(question)
        cache_file = self.cache_dir / f"{key}.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(answer, f)
        except Exception:
            pass


# Global cache instance
_cache: Optional[SimpleCache] = None

def get_cache() -> SimpleCache:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        _cache = SimpleCache()
    return _cache