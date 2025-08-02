from pathlib import Path

from langchain.schema import Document

from src.loaders import load_pdf
from src.sources.pmc import PMCSource
from src.splitters import split_text


def load_source_docs(pdf_path: Path | str | None = None, pmc_query: str | None = None, pmc_limit: int = 100) -> list[Document]:
    """
    Load PDF(s) and/or PMC papers and return split chunks with paper-level metadata.

    If pdf_path is provided, loads single PDF.
    If pdf_path is None, loads all PDFs from raw_data/ directory.
    If pmc_query is provided, fetches papers from PMC and combines with PDF sources.
    """
    all_documents = []

    # Handle PMC papers first
    if pmc_query:
        print(f"Fetching longevity papers from PMC with query: {pmc_query}")
        pmc_source = PMCSource()
        pmc_docs = pmc_source.fetch_papers(pmc_query, pmc_limit)

        # PMC papers come pre-chunked and processed, add directly
        all_documents.extend(pmc_docs)

        # Apply your existing metadata enrichment to PMC docs
        for doc in pmc_docs:
            # Mark as processed in tracker
            pmc_source.tracker.mark_processed(doc.metadata.get('paper_id'))

        print(f"Added {len(pmc_docs)} PMC papers to corpus")

    # Handle PDF sources (existing logic)
    if pdf_path:
        # Single PDF mode (backward compatibility)
        path = Path(pdf_path)
        docs = load_pdf(str(path))
        # Add paper metadata to each document
        for doc in docs:
            doc.metadata.update({
                'paper_title': path.stem,
                'source_file': path.name,
                'source_type': 'local'  # Mark as local PDF
            })
        pdf_chunks = split_text(docs)
        all_documents.extend(pdf_chunks)

    elif not pmc_query:  # Only load PDFs if no specific source requested
        # Multi-PDF mode: load all PDFs from raw_data/
        raw_data_dir = Path(__file__).parent.parent / 'raw_data'

        for pdf_file in raw_data_dir.glob('*.pdf'):
            print(f"Loading: {pdf_file.name}")
            docs = load_pdf(str(pdf_file))

            # Add paper-level metadata to each document
            for doc in docs:
                doc.metadata.update({
                    'paper_title': pdf_file.stem,
                    'source_file': pdf_file.name,
                    'source_type': 'local'  # Mark as local PDF
                })

            # Split and collect chunks
            chunks = split_text(docs)
            all_documents.extend(chunks)
            print(f"  → {len(chunks)} chunks")

    total_papers = len([doc for doc in all_documents if doc.metadata.get('source_type') == 'local'])
    total_pmc = len([doc for doc in all_documents if doc.metadata.get('source_type') == 'pmc'])

    print(f"Total documents loaded: {len(all_documents)} chunks ({total_pmc} PMC papers, {total_papers} local PDFs)")
    return all_documents
