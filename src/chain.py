from pathlib import Path
from typing import Optional

from langchain.schema import BaseRetriever  # type: ignore
from langchain_core.output_parsers import StrOutputParser  # type: ignore
from langchain_core.runnables import Runnable, RunnablePassthrough  # type: ignore
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from config import MODEL_NAME, OPENAI_API_KEY, PERSIST_DIRECTORY
from src.indexer import build_index, load_index
from src.loaders import load_pdf
from src.splitters import split_text


PROMPT_RAG: str = (
    "You are a domain‐expert AI researcher specializing in computer science, AI, ML, NLP, and Neuroscience research papers.\n"
    "Your task is to answer the user’s question using only the provided context.\n\n"
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
    persist_path = Path(PERSIST_DIRECTORY)
    if not persist_path.exists():
        pdf_path = Path(__file__).resolve().parent.parent / 'raw_data' / 'rag_intensive_nlp_tasks.pdf'
        docs = load_pdf(str(pdf_path))
        chunks = split_text(docs)
        build_index(chunks)
    index = load_index()
    retriever = index.as_retriever(search_type='similarity', search_kwargs={'k': k})
    return get_chain(retriever)
