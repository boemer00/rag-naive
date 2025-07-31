#!/usr/bin/env python3
"""
Demonstration of Multi-Document RAG capabilities
Shows how the system loads and processes multiple research papers
"""

from src.utils import load_source_docs
from collections import Counter
import json

def analyze_corpus():
    """Analyze the loaded multi-document corpus"""
    print("🔬 Multi-Document RAG Analysis")
    print("=" * 50)
    
    # Load all documents
    chunks = load_source_docs()
    
    print(f"\n📊 Corpus Statistics:")
    print(f"  • Total chunks: {len(chunks)}")
    
    # Analyze papers
    papers = set(chunk.metadata.get('paper_title', 'Unknown') for chunk in chunks)
    print(f"  • Papers loaded: {len(papers)}")
    
    for paper in sorted(papers):
        paper_chunks = [c for c in chunks if c.metadata.get('paper_title') == paper]
        print(f"    - {paper}: {len(paper_chunks)} chunks")
    
    print(f"\n🏷️  Metadata Analysis:")
    
    # Study types distribution
    study_types = Counter(chunk.metadata.get('study_type', 'unknown') for chunk in chunks)
    print(f"  • Study Types: {dict(study_types)}")
    
    # Topics distribution
    all_topics = [topic for chunk in chunks for topic in chunk.metadata.get('topics', [])]
    topics = Counter(all_topics)
    print(f"  • Topics: {dict(topics)}")
    
    # Biomarkers found
    all_biomarkers = [marker for chunk in chunks for marker in chunk.metadata.get('biomarkers', [])]
    biomarkers = Counter(all_biomarkers)
    print(f"  • Biomarkers: {dict(biomarkers)}")
    
    # Section distribution
    sections = Counter(chunk.metadata.get('section', 'unknown') for chunk in chunks)
    print(f"  • Sections: {dict(sections)}")
    
    return chunks

def simulate_queries(chunks):
    """Simulate how different queries would be filtered"""
    print(f"\n🔍 Query Simulation (Metadata Filtering):")
    print("=" * 50)
    
    # Simulate cardiovascular query
    cardio_chunks = [c for c in chunks if 'cardiovascular' in c.metadata.get('topics', [])]
    print(f"• 'cardiovascular health' → {len(cardio_chunks)} relevant chunks")
    
    # Simulate exercise query  
    exercise_chunks = [c for c in chunks if 'exercise' in c.metadata.get('topics', [])]
    print(f"• 'exercise and longevity' → {len(exercise_chunks)} relevant chunks")
    
    # Simulate meta-analysis query
    meta_chunks = [c for c in chunks if c.metadata.get('study_type') == 'meta-analysis']
    print(f"• 'meta-analysis evidence' → {len(meta_chunks)} relevant chunks")
    
    # Simulate heart rate query
    hr_chunks = [c for c in chunks if 'heart_rate' in c.metadata.get('biomarkers', [])]
    print(f"• 'heart rate biomarker' → {len(hr_chunks)} relevant chunks")
    
    # Show sample relevant content
    if cardio_chunks:
        print(f"\n📝 Sample cardiovascular content:")
        sample = cardio_chunks[0]
        print(f"  Paper: {sample.metadata.get('paper_title', 'Unknown')}")
        print(f"  Section: {sample.metadata.get('section', 'Unknown')}")
        print(f"  Content preview: {sample.page_content[:200]}...")

def show_metadata_sample(chunks):
    """Show detailed metadata structure"""
    print(f"\n🗂️  Sample Metadata Structure:")
    print("=" * 50)
    
    sample_chunk = chunks[0]
    metadata = sample_chunk.metadata
    
    # Show only the new metadata we added
    our_metadata = {
        'paper_title': metadata.get('paper_title'),
        'source_file': metadata.get('source_file'), 
        'section': metadata.get('section'),
        'study_type': metadata.get('study_type'),
        'topics': metadata.get('topics'),
        'biomarkers': metadata.get('biomarkers'),
        'is_title_page': metadata.get('is_title_page', False)
    }
    
    print(json.dumps(our_metadata, indent=2))

if __name__ == "__main__":
    chunks = analyze_corpus()
    simulate_queries(chunks)
    show_metadata_sample(chunks)
    
    print(f"\n✅ Multi-Document RAG Implementation Working!")
    print(f"   Ready for upgrade to advanced retrieval methods.")