from collections.abc import Callable
from pathlib import Path

from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from config import get_config


def _get_embedder() -> OpenAIEmbeddings:
    """Return an `OpenAIEmbeddings` instance configured with the API key."""
    config = get_config()
    return OpenAIEmbeddings(
        model=config.embedding_model,
        openai_api_key=config.openai_api_key,
    )

def ensure_index_exists(docs_loader: Callable[[], list[Document]], force: bool=False):
    """Ensure a Chroma index exists and return it.

    If the index is missing we build it and **return the in-memory instance**
    produced by :pyfunc:`build_index`, avoiding an immediate reload from disk.
    Otherwise, we just load the existing index.
    """
    from src.index_cache import get_index_cache

    config = get_config()
    persist_path = Path(config.persist_directory)
    index_cache = get_index_cache()

    if force or not persist_path.exists():
        index_cache.clear_cache()  # Clear vector index cache when rebuilding
        # Also clear response cache to avoid stale answers tied to old corpus
        try:
            from src.cache import get_cache
            get_cache().clear_all()
        except Exception:
            pass
        docs = docs_loader()
        return build_index(docs)  # single pass

    return index_cache.get_index()  # Use cached index

def build_index(docs):
    """Build a Chroma index from a list of documents with batch embedding"""
    config = get_config()
    embedder = _get_embedder()

    # Process documents in batches for better performance
    batch_size = 50  # Simple batch size
    batched_docs = [docs[i:i + batch_size] for i in range(0, len(docs), batch_size)]

    db = None
    for i, batch in enumerate(batched_docs):
        if i == 0:
            # Create initial index with first batch
            db = Chroma.from_documents(
                batch,
                embedder,
                persist_directory=config.persist_directory
            )
        else:
            # Add subsequent batches to existing index
            db.add_documents(batch)

    return db

def load_index():
    """Load a Chroma index from disk"""
    config = get_config()
    embedder = _get_embedder()
    return Chroma(
        persist_directory=config.persist_directory,
        embedding_function=embedder,
    )


## this could be a class.
