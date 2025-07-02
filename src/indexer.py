from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config import OPENAI_API_KEY, PERSIST_DIRECTORY


def build_index(docs):
    embedder = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=OPENAI_API_KEY,
    )
    db = Chroma.from_documents(
        documents=docs,
        embedding_function=embedder,
        persist_directory=PERSIST_DIRECTORY,
    )
    db.persist()
    return db

def load_index():
    embedder = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=OPENAI_API_KEY,
    )
    return Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embedder,
    )
