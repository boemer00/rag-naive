from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate


def get_retrieval_qa(llm, vectorstore):
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=(
            "You are a helpful assistant that can answer questions about the following context:\n"
            "{context}\n\n"
            "Question: {question}"
        ),
    )
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
        chain_type_kwargs={"prompt": prompt},
    )
    return chain
