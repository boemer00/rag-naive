from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config import get_openai_api_key, PERSIST_DIRECTORY, EMBEDDING_MODEL
from pathlib import Path
from typing import Callable, List
from langchain.schema import Document


def _get_embedder() -> OpenAIEmbeddings:
    """Return an `OpenAIEmbeddings` instance configured with the API key."""
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=get_openai_api_key(),
    )

def ensure_index_exists(docs_loader: Callable[[], List[Document]], force: bool=False):
    """Ensure a Chroma index exists and return it.

    If the index is missing we build it and **return the in-memory instance**
    produced by :pyfunc:`build_index`, avoiding an immediate reload from disk.
    Otherwise, we just load the existing index.
    """
    persist_path = Path(PERSIST_DIRECTORY)

    if force or not persist_path.exists():
        docs = docs_loader()
        return build_index(docs)  # single pass
    return load_index()

def build_index(docs):
    """Build a Chroma index from a list of documents"""
    embedder = _get_embedder()
    db = Chroma.from_documents(
        docs,
        embedder,
        persist_directory=PERSIST_DIRECTORY
    )
    return db

def load_index():
    """Load a Chroma index from disk"""
    embedder = _get_embedder()
    return Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embedder,
    )


## this could be a class.
