from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config import OPENAI_API_KEY, PERSIST_DIRECTORY, EMBEDDING_MODEL


def build_index(docs):
    embedder = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )

    db = Chroma.from_documents(docs, embedder, persist_directory=PERSIST_DIRECTORY)
    return db

def load_index():
    embedder = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )
    return Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embedder,
    )
