from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI

from config import get_config
from src.cache import get_cache
from src.chain import PROMPT_RAG
from src.indexer import ensure_index_exists
from src.monitoring import configure_langsmith, evaluate_and_log, trace_run
from src.retrieval import get_metadata
from src.utils import load_source_docs

configure_langsmith()


@trace_run
def answer(question: str, force_reindex: bool = False, use_cache: bool = True) -> str:
    """Return an answer to the given question using the RAG pipeline.

    Parameters
    ----------
    question : str
        Natural-language question.
    force_reindex : bool, optional
        Whether to force rebuilding the vector index, by default False.
    use_cache : bool, optional
        Whether to use cached responses, by default True.

    Returns
    -------
    str
        LLM-generated answer.
    """
    config = get_config()
    cache = get_cache()
    
    # Check cache first
    if use_cache:
        cached_answer = cache.get(question)
        if cached_answer:
            return cached_answer

    # Ensure the vector index exists (or rebuild if forced)
    index: Chroma = ensure_index_exists(load_source_docs, force_reindex)

    # Retrieve relevant documents, with metadata boosting for certain question types
    docs = get_metadata(index, question, k=config.retrieval_k)

    # Build a context string from retrieved docs
    context: str = "\n\n".join(doc.page_content for doc in docs)

    # Prepare the prompt
    prompt = PromptTemplate(
        input_variables=['context', 'question'],
        template=PROMPT_RAG,
    )

    # Instantiate LLM
    llm = ChatOpenAI(
        model=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        openai_api_key=config.openai_api_key,
    )

    # Format prompt and invoke model
    formatted_prompt: str = prompt.format(context=context, question=question)
    response = llm.invoke(formatted_prompt)
    result: str = response.content

    # Log RAG metrics to LangSmith (sample rate can be controlled via env var)
    evaluate_and_log(question, result, context)
    
    # Cache the result
    if use_cache:
        cache.set(question, result)

    return result


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        _question = ' '.join(sys.argv[1:])
    else:
        _question = input('Enter your question: ')

    print('Thinking...\n')
    _answer = answer(_question)
    print(_answer)
