from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

def split_text(docs, chunk_size: int=1000, chunk_overlap: int=200):
    splitter = RecursiveCharacterTextSplitter(
        separators=['\n\n', '\n', ' '],
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

        # Simple flag for first page (likely contains title)
        if chunk.metadata.get('page', 999) == 0:
            chunk.metadata['is_title_page'] = True

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
        
        # Add longevity-specific metadata based on content analysis
        content_lower = chunk.page_content.lower()
        
        # Detect research type keywords
        if any(term in content_lower for term in ['meta-analysis', 'systematic review']):
            chunk.metadata['study_type'] = 'meta-analysis'
        elif any(term in content_lower for term in ['randomized', 'clinical trial', 'rct']):
            chunk.metadata['study_type'] = 'rct'
        elif any(term in content_lower for term in ['cohort', 'longitudinal', 'observational']):
            chunk.metadata['study_type'] = 'observational'
        else:
            chunk.metadata['study_type'] = 'general'
        
        # Detect longevity topics
        topics = []
        if any(term in content_lower for term in ['cardiovascular', 'heart', 'blood pressure', 'cardiac']):
            topics.append('cardiovascular')
        if any(term in content_lower for term in ['sleep', 'circadian', 'insomnia']):
            topics.append('sleep')
        if any(term in content_lower for term in ['exercise', 'physical activity', 'fitness', 'training']):
            topics.append('exercise')
        if any(term in content_lower for term in ['nutrition', 'diet', 'food', 'caloric restriction']):
            topics.append('nutrition')
        if any(term in content_lower for term in ['aging', 'longevity', 'lifespan', 'mortality']):
            topics.append('longevity')
        
        chunk.metadata['topics'] = ','.join(topics) if topics else 'general'
        
        # Detect biomarkers mentioned
        biomarkers = []
        if any(term in content_lower for term in ['heart rate', 'hr', 'pulse']):
            biomarkers.append('heart_rate')
        if any(term in content_lower for term in ['blood pressure', 'bp', 'hypertension']):
            biomarkers.append('blood_pressure')
        if any(term in content_lower for term in ['vo2', 'oxygen consumption', 'aerobic capacity']):
            biomarkers.append('vo2_max')
        if any(term in content_lower for term in ['sleep quality', 'sleep duration', 'rem']):
            biomarkers.append('sleep_metrics')
        
        chunk.metadata['biomarkers'] = ','.join(biomarkers) if biomarkers else ''

    return chunks

if __name__ == '__main__':
    from loaders import load_pdf
    docs = load_pdf('raw_data/rag_intensive_nlp_tasks.pdf')
    chunks = split_text(docs)
    print(f'Total chunks: {len(chunks)}')
    print('First chunk metadata:', chunks[0].metadata)
    print('First chunk content:', chunks[0].page_content[:100])
