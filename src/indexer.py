from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config import OPENAI_API_KEY, PERSIST_DIRECTORY


def build_index(docs):
    embedder = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=OPENAI_API_KEY,
    )
    # NOTE: Passing the embedding function POSITIONALLY avoids an upstream bug in
    # `Chroma.from_documents` where providing it as a keyword results in
    # `TypeError: got multiple values for keyword argument 'embedding_function'`.
    db = Chroma.from_documents(docs, embedder, persist_directory=PERSIST_DIRECTORY)
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
