from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain.schema import Document

def split_text(text: List[Document], chunk_size: int=1000, chunk_overlap: int=200):
    splitter = RecursiveCharacterTextSplitter(
        separators=['\n\n', '\n', ' ', ''],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_documents(docs)

if __name__ == '__main__':
    from src.loaders import load_pdf
    docs = load_pdf('raw_data/rag_intensive_nlp_tasks.pdf')
    chunks = split_text(docs)
    print(f"Total chunks: {len(chunks)}")
    print(chunks[0].page_content[:100])
