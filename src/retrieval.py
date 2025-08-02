# src/retrieval.py

from langchain.schema import Document
from langchain_chroma import Chroma


def get_metadata(index: Chroma, question: str, k: int=6) -> list[Document]:
    """Return top-k documents with metadata, a boosting for title/author queries"""
    # Normalize question for keyword checks
    question_lower = question.lower()

    # Perform standard semantic retrieval
    retriever = index.as_retriever(search_type='similarity', search_kwargs={'k': k})
    semantic_docs: list[Document] = retriever.invoke(question)

    # Heuristic: If the user asks about title or author information, boost metadata
    boost_keywords = [
        'title',
        'name of paper',
        'paper title',
        'author',
        'wrote',
        'written by',
    ]

    if any(word in question_lower for word in boost_keywords):
        try:
            # Retrieve docs from the first page (typically contains title/author)
            page_0_results = index.get(where={'page': 0})

            if page_0_results and 'documents' in page_0_results:
                page_0_docs: list[Document] = []

                for i, doc_text in enumerate(page_0_results['documents']):
                    # Preserve metadata if available
                    metadata = {}
                    if 'metadatas' in page_0_results and i < len(page_0_results["metadatas"]):
                        metadata = page_0_results['metadatas'][i]

                    page_0_docs.append(Document(page_content=doc_text, metadata=metadata))

                # Combine: page-0 docs first, followed by semantic docs not already included
                combined_docs: list[Document] = page_0_docs.copy()

                for doc in semantic_docs:
                    if not any(d.page_content[:100] == doc.page_content[:100] for d in combined_docs):
                        combined_docs.append(doc)

                return combined_docs[:k]
        except Exception as exc:
            # Gracefully fall back to semantic results on any retrieval error
            print(f'Error retrieving page 0 docs: {exc}')

    # Default fallback: return semantic results
    return semantic_docs
