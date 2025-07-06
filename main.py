from typing import List

from config import MODEL_NAME, get_openai_api_key
from langchain.schema import Document
from langchain_chroma import Chroma
from src.monitoring import configure_langsmith, trace_run

from src.chain import PROMPT_RAG
from src.indexer import ensure_index_exists

from src.utils import load_source_docs
from src.retrieval import get_metadata

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

configure_langsmith()


@trace_run
def answer(question: str, force_reindex: bool = False) -> str:
    """Return an answer to the given question using the RAG pipeline.

    Parameters
    ----------
    question : str
        Natural-language question.
    force_reindex : bool, optional
        Whether to force rebuilding the vector index, by default False.

    Returns
    -------
    str
        LLM-generated answer.
    """
    # Ensure the vector index exists (or rebuild if forced)
    index: Chroma = ensure_index_exists(load_source_docs, force_reindex)

    # Retrieve relevant documents, with metadata boosting for certain question types
    docs = get_metadata(index, question, k=6)

    # Build a context string from retrieved docs
    context: str = "\n\n".join(doc.page_content for doc in docs)

    # Prepare the prompt
    prompt = PromptTemplate(
        input_variables=['context', 'question'],
        template=PROMPT_RAG,
    )

    # Instantiate LLM
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.0,
        max_tokens=512,
        openai_api_key=get_openai_api_key(),
    )

    # Format prompt and invoke model
    formatted_prompt: str = prompt.format(context=context, question=question)
    response = llm.invoke(formatted_prompt)

    return response.content


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        _question = ' '.join(sys.argv[1:])
    else:
        _question = input('Enter your question: ')

    print('Thinking...\n')
    _answer = answer(_question)
    print(_answer)
