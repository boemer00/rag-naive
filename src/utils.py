from pathlib import Path
from typing import List
from langchain.schema import Document
from src.loaders import load_pdf
from src.splitters import split_text


def load_source_docs(pdf_path: Path | str | None = None) -> List[Document]:
    """
    Load PDF(s) and return split chunks with paper-level metadata.
    
    If pdf_path is provided, loads single PDF.
    If pdf_path is None, loads all PDFs from raw_data/ directory.
    """
    if pdf_path:
        # Single PDF mode (backward compatibility)
        path = Path(pdf_path)
        docs = load_pdf(str(path))
        # Add paper metadata to each document
        for doc in docs:
            doc.metadata.update({
                'paper_title': path.stem,
                'source_file': path.name
            })
        return split_text(docs)
    
    # Multi-PDF mode: load all PDFs from raw_data/
    raw_data_dir = Path(__file__).parent.parent / 'raw_data'
    all_chunks = []
    
    for pdf_file in raw_data_dir.glob('*.pdf'):
        print(f"Loading: {pdf_file.name}")
        docs = load_pdf(str(pdf_file))
        
        # Add paper-level metadata to each document
        for doc in docs:
            doc.metadata.update({
                'paper_title': pdf_file.stem,
                'source_file': pdf_file.name
            })
        
        # Split and collect chunks
        chunks = split_text(docs)
        all_chunks.extend(chunks)
        print(f"  → {len(chunks)} chunks")
    
    print(f"Total documents loaded: {len(all_chunks)} chunks from {len(list(raw_data_dir.glob('*.pdf')))} papers")
    return all_chunks
