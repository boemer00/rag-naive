#!/usr/bin/env python3
"""Simple CLI for health data analysis using RAG + biomarkers."""

import argparse
import sys
from pathlib import Path

from src.mcp.apple_health import get_latest_metrics
from src.mcp.health_analyzer import analyze_health_metrics, get_biomarker_insights


def main():
    parser = argparse.ArgumentParser(description='Analyze health data with longevity research')
    parser.add_argument('--health-export', required=True,
                       help='Path to Apple Health export.xml file')
    parser.add_argument('--question',
                       help='Custom question about your health metrics')
    parser.add_argument('--biomarker', choices=['vo2_max', 'heart_rate', 'sleep'],
                       help='Get insights for specific biomarker')
    parser.add_argument('--summary', action='store_true',
                       help='Show health metrics summary')

    args = parser.parse_args()

    # Validate health file exists
    health_file = Path(args.health_export)
    if not health_file.exists():
        print(f"Error: Health export file not found: {health_file}")
        sys.exit(1)

    try:
        if args.summary:
            # Show health metrics summary
            health_data = get_latest_metrics(str(health_file))
            print("Health Metrics Summary")
            print("=" * 40)

            if health_data.get("avg_resting_hr"):
                print(f"Average Resting HR: {health_data['avg_resting_hr']:.1f} bpm")

            if health_data.get("latest_vo2_max"):
                print(f"Latest VO2 Max: {health_data['latest_vo2_max']:.1f} ml/kg/min")

            if health_data.get("avg_sleep_duration"):
                print(f"Average Sleep: {health_data['avg_sleep_duration']:.1f} hours")

            if health_data.get("date_range"):
                print(f"Data Period: {health_data['date_range']}")

        elif args.biomarker:
            # Analyze specific biomarker
            print(f"Analyzing {args.biomarker} with longevity research...")
            print("=" * 60)
            result = get_biomarker_insights(str(health_file), args.biomarker)
            print(result)

        elif args.question:
            # Custom question analysis
            print("Analyzing your health data with research papers...")
            print("=" * 60)
            result = analyze_health_metrics(str(health_file), args.question)
            print(result)

        else:
            print("Please specify --summary, --biomarker, or --question")
            parser.print_help()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
