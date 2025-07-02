from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY, MODEL_NAME, CHAIN_TYPE
from src.indexer import load_index

# 1) initialize the LLM
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=0,
    max_tokens=512,
    openai_api_key=OPENAI_API_KEY,
)

# 2) create a retriever from the VectorStore
vector_store = load_index()  # returns a Chroma instance
retriever = vector_store.as_retriever(
    search_type='similarity',
    search_kwargs={'k': 2},
)

# 3) define a function to build the RetrievalQA chain
def get_retrieval_qa(llm, retriever):
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=(
            "Use the following pieces of context to answer the question at the end."
            "If you don't know the answer, say you don't know it.\n\n"
            "Context: {context}\n\n"
            "Question: {question}\n\n"
        ),
    )
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type=CHAIN_TYPE,
        retriever=retriever,
        chain_type_kwargs={'prompt': prompt},
    )
