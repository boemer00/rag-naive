from pathlib import Path
from typing import List

from config import PERSIST_DIRECTORY, OPENAI_API_KEY, MODEL_NAME
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from src.indexer import build_index, load_index
from src.loaders import load_pdf
from src.splitters import split_text


# ---------------------------------------------------------------------------
# Source document loading
# ---------------------------------------------------------------------------

def load_source_docs() -> List[Document]:
    """Load and split the sample PDF in raw_data/."""
    pdf_path = Path(__file__).parent / 'raw_data' / 'rag_intensive_nlp_tasks.pdf'
    docs = load_pdf(str(pdf_path))
    return split_text(docs)


# ---------------------------------------------------------------------------
# Vector index management
# ---------------------------------------------------------------------------

def ensure_index(force: bool = False) -> Chroma:
    """Return a persisted Chroma index, creating it from source docs if required."""
    persist_path = Path(PERSIST_DIRECTORY)

    if force or not persist_path.exists():
        docs = load_source_docs()
        build_index(docs)

    return load_index()


# ---------------------------------------------------------------------------
# Chain construction
# ---------------------------------------------------------------------------

def build_chain(retriever) -> Runnable:
    """Assemble an LCEL chain (context → prompt → LLM → output parser)."""
    prompt = PromptTemplate(
        input_variables=['context', 'question'],
        template=(
            "Use the following pieces of context to answer the question at the end.\n"
            "If you don't know the answer, just say you don't know.\n\n"
            "Context: {context}\n\n"
            "Question: {question}\n\n"
        ),
    )

    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0,
        max_tokens=512,
        openai_api_key=OPENAI_API_KEY,
    )

    return (
        {'context': retriever, 'question': RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )


# ---------------------------------------------------------------------------
# High-level helper
# ---------------------------------------------------------------------------

def answer(question: str, force_reindex: bool = False) -> str:
    """Ensure the index exists, run the chain for the given question, and return the answer."""
    index = ensure_index(force=force_reindex)
    retriever = index.as_retriever(search_type='similarity', search_kwargs={'k': 2})
    chain = build_chain(retriever)
    return chain.invoke(question)


# ---------------------------------------------------------------------------
# CLI entry-point (minimal, no full CLI dependency)
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        _question = ' '.join(sys.argv[1:])
    else:
        _question = input('Enter your question: ')

    print('Thinking…\n')
    _answer = answer(_question)
    print(_answer)
