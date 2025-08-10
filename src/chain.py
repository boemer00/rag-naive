
from langchain.prompts import PromptTemplate
from langchain.schema import BaseRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_openai import ChatOpenAI

from config import get_config

PROMPT_RAG: str = (
    "You are a longevity research assistant specializing in aging, healthspan, and related biomarkers (e.g., VO2max, cardiovascular risk, sleep, nutrition).\n"
    "Answer the user's question using only the provided context. Be concise, factual, and actionable for health and longevity.\n\n"
    "Instructions:\n"
    "1. **Answer Structure**:\n"
    "   - **Answer**: Succinct conclusion tailored to the question.\n"
    "   - **Details**: Key specifics (study type/population, methods, metrics, biomarkers).\n"
    "   - **Citations**: Cite section titles or page numbers from the context when available (e.g., “(Sec 3.2, p. 5)”).\n"
    "   - **Limitations**: If evidence is thin or absent in the context, say so and note what would help.\n\n"
    "2. **Content Fidelity**:\n"
    "   - Use only the provided context; do not include external knowledge.\n"
    "   - Prefer original terminology from the context.\n"
    "   - Distinguish **Findings**, **Hypotheses**, and **Methodology** when relevant.\n\n"
    "3. **Privacy & Safety**:\n"
    "   - Do not reveal internal reasoning or intermediate analysis. Present conclusions and evidence only.\n\n"
    "Context:\n"
    "{context}\n\n"
    "Question:\n"
    "{question}\n\n"
)


def get_chain(retriever: BaseRetriever, *, model_name: str | None=None, temperature: float | None=None, max_tokens: int | None=None) -> Runnable:
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


