from langchain_community.document_loaders import PyPDFLoader

def load_pdf(file_path: str):
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    return docs


if __name__ == '__main__':
    docs = load_pdf('raw_data/rag_intensive_nlp_tasks.pdf')
    print(f'Total pages: {len(docs)}')
    print(docs[0].page_content[:100])
    print(docs[0].metadata)
