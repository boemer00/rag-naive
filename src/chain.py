from typing import Optional

from langchain.schema import BaseRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from config import MODEL_NAME, OPENAI_API_KEY
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


def get_chain(retriever: BaseRetriever, *, model_name: Optional[str]=None, temperature: float=0.0, max_tokens: int=512) -> Runnable:
    """Builds a RAG chain: Retriever → Prompt → LLM → String parser."""
    prompt = PromptTemplate(
        input_variables=['context', 'question'],
        template=PROMPT_RAG,
    )
    llm = ChatOpenAI(
        model=model_name or MODEL_NAME,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_api_key=OPENAI_API_KEY,
    )
    return (
        {'context': retriever, 'question': RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )


def build_default_chain(*, k: int = 2) -> Runnable:
    """Ensures index exists (build from PDF if needed) and returns the default RAG chain."""
    index = ensure_index_exists(load_source_docs)
    retriever = index.as_retriever(search_type='similarity', search_kwargs={'k': k})
    return get_chain(retriever)
