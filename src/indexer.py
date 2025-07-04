from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config import OPENAI_API_KEY, PERSIST_DIRECTORY, EMBEDDING_MODEL
from pathlib import Path
from typing import Callable, List
from langchain.schema import Document


def _get_embedder():
    """Get an OpenAI embedder"""
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )

def ensure_index_exists(docs_loader: Callable[[], List[Document]], force: bool=False):
    """Ensure a Chroma index exists on disk"""
    persist_path = Path(PERSIST_DIRECTORY)

    if force or not persist_path.exists():
        docs = docs_loader()
        build_index(docs)
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
