#!/usr/bin/env python3
"""
Inspect the longevity papers database.
Shows statistics and sample papers from the SQLite database.
"""

from src.sources.paper_tracker import PaperTracker
import argparse
import json


def main():
    parser = argparse.ArgumentParser(description='Inspect longevity papers database')
    parser.add_argument('--sample', type=int, default=5,
                       help='Number of sample papers to show (default: 5)')
    parser.add_argument('--unprocessed', action='store_true',
                       help='Show only unprocessed papers')
    args = parser.parse_args()
    
    tracker = PaperTracker()
    
    print("=" * 60)
    print("Longevity Papers Database Inspector")
    print("=" * 60)
    
    # Show statistics
    stats = tracker.get_stats()
    print("\nDatabase Statistics:")
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    # Show sample papers
    if args.unprocessed:
        papers = tracker.get_unprocessed_papers(limit=args.sample)
        print(f"\nSample Unprocessed Papers ({len(papers)}):")
    else:
        # Get all papers for sampling
        import sqlite3
        with sqlite3.connect(tracker.db_path) as conn:
            cursor = conn.execute(f"SELECT * FROM papers LIMIT {args.sample}")
            columns = [desc[0] for desc in cursor.description]
            papers = []
            for row in cursor.fetchall():
                paper = dict(zip(columns, row))
                if paper['authors']:
                    paper['authors'] = json.loads(paper['authors'])
                if paper['keywords']:
                    paper['keywords'] = json.loads(paper['keywords'])
                papers.append(paper)
        
        print(f"\nSample Papers ({len(papers)}):")
    
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper['title'][:80]}{'...' if len(paper['title']) > 80 else ''}")
        # Handle authors field safely
        authors = paper['authors']
        if authors:
            if isinstance(authors[0], dict):
                # Authors are dict objects with 'name' field
                author_str = ', '.join([author.get('name', 'Unknown') for author in authors[:3]])
            else:
                # Authors are strings
                author_str = ', '.join(authors[:3])
        else:
            author_str = 'Unknown'
        print(f"   Authors: {author_str}")
        print(f"   Journal: {paper['journal']}")
        print(f"   Date: {paper['pub_date']}")
        print(f"   PMC ID: {paper['pmc_id']}")
        print(f"   Source: {paper['source_type']}")
        print(f"   Processed: {'✅' if paper['processed'] else '❌'}")
        if paper['abstract']:
            print(f"   Abstract: {paper['abstract'][:100]}{'...' if len(paper['abstract']) > 100 else ''}")
    
    if not papers:
        print("\nNo papers found in database. Run fetch_longevity_papers.py first.")


if __name__ == "__main__":
    main()