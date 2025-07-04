from pathlib import Path
from typing import List
from langchain.schema import Document
from src.loaders import load_pdf
from src.splitters import split_text
from config import SAMPLE_PDF


def load_source_docs(pdf_path: Path | str | None = None) -> List[Document]:
    """
    Load the sample PDF and return split chunks.
    Intended primarily for demos and tests; callers may override pdf_path.
    """
    path = Path(pdf_path) if pdf_path else SAMPLE_PDF
    docs = load_pdf(str(path))
    return split_text(docs)
