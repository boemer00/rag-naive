from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain.schema import Document
import re

def split_text(docs, chunk_size: int=1000, chunk_overlap: int=200):
    splitter = RecursiveCharacterTextSplitter(
        separators=['\n\n', '\n', ' ', ''],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(docs)

    # Add section metadata to chunks
    section_patterns = [
        r'^\s*(?:abstract|summary)\s*$',
        r'^\s*(?:\d+\.?\s*)?introduction\s*$',
        r'^\s*(?:\d+\.?\s*)?(?:methods?|methodology)\s*$',
        r'^\s*(?:\d+\.?\s*)?(?:results?|findings?)\s*$',
        r'^\s*(?:\d+\.?\s*)?discussion\s*$',
        r'^\s*(?:\d+\.?\s*)?conclusion\s*$',
        r'^\s*(?:\d+\.?\s*)?references?\s*$',
    ]

    for chunk in chunks:
        # Find section headers in the chunk
        lines = chunk.page_content.split('\n')
        detected_section = 'content'  # default

        for line in lines[:3]:  # Check first few lines
            line_clean = line.strip().lower()
            for pattern in section_patterns:
                if re.match(pattern, line_clean, re.IGNORECASE):
                    detected_section = re.sub(r'^\s*(?:\d+\.?\s*)?', '', line_clean).strip()
                    break
            if detected_section != 'content':
                break

        # Add section metadata
        chunk.metadata['section'] = detected_section

    return chunks

if __name__ == '__main__':
    from loaders import load_pdf
    docs = load_pdf('raw_data/rag_intensive_nlp_tasks.pdf')
    chunks = split_text(docs)
    print(f"Total chunks: {len(chunks)}")
    print(chunks[0].page_content[:100])
