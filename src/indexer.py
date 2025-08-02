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
    config = get_config()
    persist_path = Path(config.persist_directory)

    if force or not persist_path.exists():
        docs = docs_loader()
        return build_index(docs)  # single pass
    return load_index()

def build_index(docs):
    """Build a Chroma index from a list of documents"""
    config = get_config()
    embedder = _get_embedder()
    db = Chroma.from_documents(
        docs,
        embedder,
        persist_directory=config.persist_directory
    )
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
