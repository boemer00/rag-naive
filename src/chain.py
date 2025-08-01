from typing import Optional

from langchain.schema import BaseRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from config import get_config, get_openai_api_key
from src.indexer import ensure_index_exists
from src.utils import load_source_docs


PROMPT_RAG: str = (
    "You are a domain-expert AI researcher specializing in computer science, AI, ML, NLP, and Neuroscience research papers.\n"
    "Your task is to answer the user's question using only the provided context.\n\n"
    "Instructions:\n"
    "1. **Answer Structure**:\n"
    "   - **Answer**: Begin with a succinct summary.\n"
    "   - **Details**: Provide technical specifics—methods, datasets, metrics.\n"
    "   - **Citations**: Reference section headings or page numbers (e.g., “(Sec 3.2, p. 5)”).\n"
    "   - **Limitations**: If uncertain, preface with “Based on the provided context” and note gaps.\n\n"
    "2. **Content Fidelity**:\n"
    "   - Preserve original terminology (e.g., “stochastic gradient descent,” “transformer encoder”).\n"
    "   - Distinguish **Findings**, **Hypotheses**, and **Methodology** explicitly.\n\n"
    "3. **Reasoning**:\n"
    "   - Show brief chain-of-thought: describe how you located and interpreted context snippets.\n\n\n"
    "Context:\n"
    "{context}\n\n"
    "Question:\n"
    "{question}\n\n"
)


def get_chain(retriever: BaseRetriever, *, model_name: Optional[str]=None, temperature: Optional[float]=None, max_tokens: Optional[int]=None) -> Runnable:
    """Builds a RAG chain: Retriever → Prompt → LLM → String parser."""
    config = get_config()
    
    prompt = PromptTemplate(
        input_variables=['context', 'question'],
        template=PROMPT_RAG,
    )
    llm = ChatOpenAI(
        model=model_name or config.model_name,
        temperature=temperature if temperature is not None else config.temperature,
        max_tokens=max_tokens if max_tokens is not None else config.max_tokens,
        openai_api_key=config.openai_api_key,
    )
    return (
        {'context': retriever, 'question': RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )


def build_default_chain(*, k: Optional[int] = None) -> Runnable:
    """Ensures index exists (build from PDF if needed) and returns the default RAG chain."""
    config = get_config()
    index = ensure_index_exists(load_source_docs)
    retriever = index.as_retriever(
        search_type='similarity', 
        search_kwargs={'k': k if k is not None else config.retrieval_k}
    )
    return get_chain(retriever)
