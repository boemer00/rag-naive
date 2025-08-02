#!/usr/bin/env python3
"""
Fetch the 100 most important longevity research papers from PMC.
This script uses the PMC integration to build a comprehensive longevity research database.
"""

import argparse

from src.indexer import ensure_index_exists
from src.sources.pmc import PMCSource
from src.utils import load_source_docs


def main():
    parser = argparse.ArgumentParser(description='Fetch longevity papers from PMC')
    parser.add_argument('--limit', type=int, default=100,
                       help='Number of papers to fetch (default: 100)')
    parser.add_argument('--query', type=str,
                       default='longevity aging healthspan lifespan mortality',
                       help='Search query for longevity papers')
    parser.add_argument('--force-rebuild', action='store_true',
                       help='Force rebuild the vector index')
    args = parser.parse_args()

    print("=" * 60)
    print("PMC Longevity Paper Fetcher")
    print("=" * 60)

    # Initialize PMC source to show stats
    pmc_source = PMCSource()

    print("\nCurrent database statistics:")
    stats = pmc_source.get_stats()
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")

    # Fetch papers using the extended load_source_docs function
    print(f"\nFetching {args.limit} longevity papers from PMC...")
    print(f"Query: {args.query}")

    def docs_loader():
        return load_source_docs(pmc_query=args.query, pmc_limit=args.limit)

    # Build/update the vector index
    print("\nBuilding vector index...")
    db = ensure_index_exists(docs_loader, force=args.force_rebuild)

    # Show final statistics
    print("\nFinal database statistics:")
    final_stats = pmc_source.get_stats()
    for key, value in final_stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")

    # Show collection stats
    print(f"\nVector database collection size: {db._collection.count()} documents")

    print("\n✅ Longevity paper corpus successfully built!")
    print("\nYou can now run queries with:")
    print("  python main.py 'What factors influence longevity?'")
    print("\nOr check the papers database at: papers.db")


if __name__ == "__main__":
    main()
