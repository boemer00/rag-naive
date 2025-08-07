#!/usr/bin/env python3
"""
Fetch specific VO2max and longevity research papers by PMC ID.
Adds 20 high-impact papers focused on cardiorespiratory fitness and mortality.
"""

import time

from src.indexer import ensure_index_exists
from src.sources.pmc import PMCSource
from src.utils import load_source_docs

# 20 VO2max + Longevity papers with PMC IDs
VO2MAX_PAPERS = [
    "PMC9934752",  # Greater physical fitness (Vo2Max) in healthy older adults
    "PMC6324439",  # Association of Cardiorespiratory Fitness With Long-term Mortality
    "PMC9517884",  # The Impact of Training on the Loss of Cardiorespiratory Fitness
    "PMC5524050",  # Cardiorespiratory Fitness and All-cause Mortality in Men
    "PMC10856621", # Long-Term Mortality Risk According to Cardiorespiratory Fitness
    "PMC8489355",  # Non-exercise estimated cardiorespiratory fitness and mortality
    "PMC11262390", # Cardiorespiratory Fitness and Health Outcomes Across Demographics
    "PMC6592480",  # Estimating Maximal Oxygen Uptake From Daily Activity Data
    "PMC10121111", # Training Strategies to Optimize Cardiovascular Durability
    "PMC8751147",  # Cardiovascular Risk Factors and Physical Activity for Prevention
    "PMC8855984",  # Impact of Physical Activity on All-Cause Mortality
    "PMC5399980",  # Peak Oxygen Consumption and Long-Term All-Cause Mortality
    "PMC9975246",  # Age-related decline in peak oxygen uptake
    "PMC8318425",  # All‐cause mortality predicted by peak oxygen uptake
    "PMC8011752",  # Body fat predicts exercise capacity in Type 2 Diabetes
    "PMC8984568",  # Protective effects of physical activity against health risks
    "PMC7955627",  # Evaluation of metabolic equivalents of task (METs)
    "PMC6699591",  # Dose-response associations between physical activity and mortality
    "PMC10342748", # Prognostic Role of Metabolic Exercise Testing in Heart Failure
    "PMC7835615"   # Predicting maximal oxygen uptake from the 6 min walk test
]


def fetch_specific_papers(pmc_ids: list[str]) -> list:
    """Fetch specific papers by PMC ID."""
    pmc_source = PMCSource()
    documents = []

    print(f"Fetching {len(pmc_ids)} specific VO2max papers...")

    for i, pmc_id in enumerate(pmc_ids):
        print(f"Processing {i+1}/{len(pmc_ids)}: {pmc_id}")

        # Skip if already stored
        if pmc_source.is_paper_stored(pmc_id):
            print(f"  Skipping {pmc_id} - already stored")
            continue

        # Create paper dict for PMC processing
        paper = {
            'pmc_id': pmc_id,
            'pmid': '',
            'title': 'VO2max and Longevity Research',  # Will be updated from PMC
            'authors': [],
            'journal': '',
            'pub_date': '',
            'doi': '',
            'abstract': ''
        }

        # Get content from PMC
        content = pmc_source._get_paper_content(paper)
        if content:
            # Store metadata
            pmc_source._store_paper_metadata(paper, content)

            # Create document
            doc = pmc_source._create_document(paper, content)
            if doc:
                documents.append(doc)
        else:
            print(f"  Failed to fetch content for {pmc_id}")

        # Rate limiting
        time.sleep(0.5)

    return documents


def main():
    print("=" * 60)
    print("VO2max + Longevity Paper Fetcher")
    print("=" * 60)

    # Show current stats
    pmc_source = PMCSource()
    print("\nCurrent database statistics:")
    stats = pmc_source.get_stats()
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")

    # Fetch specific VO2max papers
    new_docs = fetch_specific_papers(VO2MAX_PAPERS)

    if new_docs:
        print(f"\nFetched {len(new_docs)} new VO2max papers")

        # Update vector index
        print("Updating vector index...")

        def docs_loader():
            # Load existing docs plus new ones
            existing_docs = load_source_docs()
            return existing_docs + new_docs

        db = ensure_index_exists(docs_loader, force=True)

        # Show final stats
        print("\nFinal database statistics:")
        final_stats = pmc_source.get_stats()
        for key, value in final_stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

        print(f"\nVector database collection size: {db._collection.count()} documents")
        print("\n✅ VO2max papers successfully added!")
    else:
        print("\nNo new papers to add - all already in database")

    print("\nYou can now test VO2max analysis with:")
    print("  python health_analysis.py --health-export export.xml --biomarker vo2_max")


if __name__ == "__main__":
    main()
