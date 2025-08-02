#!/usr/bin/env python3
"""
Comprehensive RAG vs Direct LLM Test Suite with Metrics.
Tests multiple question types and provides quantitative evaluation.
"""

import re
import subprocess
import sys
import time
from dataclasses import dataclass

import openai

from config import get_config


@dataclass
class TestQuestion:
    """Test question with metadata for evaluation."""
    question: str
    category: str
    expected_rag_strength: str  # "high", "medium", "low"
    description: str


@dataclass
class ComparisonResult:
    """Results of RAG vs LLM comparison."""
    question: str
    category: str
    rag_answer: str
    llm_answer: str
    rag_response_time: float
    llm_response_time: float
    rag_has_citations: bool
    rag_word_count: int
    llm_word_count: int
    rag_specificity_score: float
    llm_specificity_score: float


# Test questions covering different scenarios
TEST_QUESTIONS = [
    TestQuestion(
        question="What is the relationship between epigenetic aging and longevity? How does DNA methylation relate to biological age?",
        category="Covered by PMC Research",
        expected_rag_strength="high",
        description="Should leverage our Nature Communications paper on epigenetic aging"
    ),
    TestQuestion(
        question="How do environmental factors and the exposome influence healthy aging and longevity?",
        category="Covered by PMC Research",
        expected_rag_strength="high",
        description="Should use our Nutrients paper on environmental exposome"
    ),
    TestQuestion(
        question="What interventions have been shown to extend lifespan and healthspan in model organisms like C. elegans and mice?",
        category="Covered by PMC Research",
        expected_rag_strength="high",
        description="Should reference our multiple model organism studies"
    ),
    TestQuestion(
        question="What should I do to improve longevity if my VO2max is at 47? I'm a 43 year old male.",
        category="Not in Current Research",
        expected_rag_strength="low",
        description="Should demonstrate RAG's honesty about knowledge gaps"
    ),
    TestQuestion(
        question="How does the IGF-1 pathway relate to longevity and aging?",
        category="Partially Covered",
        expected_rag_strength="medium",
        description="We have some IGF-1 research but may not be comprehensive"
    ),
    TestQuestion(
        question="What are the latest breakthrough drugs for extending human lifespan in 2025?",
        category="Not in Current Research",
        expected_rag_strength="low",
        description="Should show RAG's limitations vs LLM speculation"
    )
]


class RAGvsLLMTester:
    """Test suite for comparing RAG and Direct LLM performance."""

    def __init__(self):
        self.config = get_config()
        self.client = openai.OpenAI(api_key=self.config.openai_api_key)
        self.results: list[ComparisonResult] = []

    def get_rag_answer(self, question: str) -> tuple[str, float]:
        """Get answer from RAG system with timing."""
        start_time = time.time()
        try:
            result = subprocess.run([
                sys.executable, 'main.py', question
            ], capture_output=True, text=True, cwd='/Users/renatoboemer/code/developer/rag-naive')

            response_time = time.time() - start_time

            if result.returncode == 0:
                return result.stdout.strip(), response_time
            else:
                return f"Error: {result.stderr}", response_time
        except Exception as e:
            return f"Error: {e}", time.time() - start_time

    def get_llm_answer(self, question: str) -> tuple[str, float]:
        """Get direct LLM answer with timing."""
        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {'role': 'system', 'content': 'You are a helpful assistant providing health and longevity advice.'},
                    {'role': 'user', 'content': question}
                ],
                temperature=0.0,
                max_tokens=512
            )

            response_time = time.time() - start_time
            return response.choices[0].message.content, response_time
        except Exception as e:
            return f"Error: {e}", time.time() - start_time

    def analyze_citations(self, text: str) -> bool:
        """Check if response contains academic citations."""
        citation_patterns = [
            r'\([A-Za-z]+.*?\d{4}\)',  # (Author, 2023)
            r'Sec\s+\d+',              # Sec 3.2
            r'p\.\s*\d+',              # p. 5
            r'\[\d+\]',                # [1]
            r'et al\.',                # et al.
            r'References?:',           # References:
            r'Citations?:'             # Citations:
        ]

        return any(re.search(pattern, text) for pattern in citation_patterns)

    def calculate_specificity_score(self, text: str) -> float:
        """Calculate specificity score based on technical terms and numbers."""
        # Technical longevity terms
        technical_terms = [
            'telomere', 'methylation', 'epigenetic', 'senescence', 'autophagy',
            'mitochondrial', 'oxidative stress', 'inflammation', 'proteome',
            'genomic', 'biomarker', 'lifespan', 'healthspan', 'caloric restriction',
            'sirtuins', 'mTOR', 'IGF-1', 'FOXO', 'p53', 'DNA damage'
        ]

        # Count technical terms
        tech_count = sum(1 for term in technical_terms if term.lower() in text.lower())

        # Count numbers (specific data points)
        number_count = len(re.findall(r'\b\d+\.?\d*%?\b', text))

        # Count specific research indicators
        research_indicators = ['study', 'research', 'analysis', 'experiment', 'trial', 'data']
        research_count = sum(1 for term in research_indicators if term.lower() in text.lower())

        # Normalize by text length (per 100 words)
        word_count = len(text.split())
        if word_count == 0:
            return 0.0

        specificity = (tech_count * 2 + number_count + research_count) / (word_count / 100)
        return min(specificity, 10.0)  # Cap at 10

    def run_comparison(self, question: TestQuestion) -> ComparisonResult:
        """Run comparison for a single question."""
        print(f"\n{'='*60}")
        print(f"Testing: {question.category}")
        print(f"Question: {question.question[:80]}...")
        print(f"{'='*60}")

        # Get RAG answer
        print("🔬 Getting RAG answer...")
        rag_answer, rag_time = self.get_rag_answer(question.question)

        # Get LLM answer
        print("🤖 Getting LLM answer...")
        llm_answer, llm_time = self.get_llm_answer(question.question)

        # Analyze responses
        rag_citations = self.analyze_citations(rag_answer)
        rag_words = len(rag_answer.split())
        llm_words = len(llm_answer.split())
        rag_specificity = self.calculate_specificity_score(rag_answer)
        llm_specificity = self.calculate_specificity_score(llm_answer)

        print(f"✅ Completed in {rag_time:.2f}s (RAG) + {llm_time:.2f}s (LLM)")

        return ComparisonResult(
            question=question.question,
            category=question.category,
            rag_answer=rag_answer,
            llm_answer=llm_answer,
            rag_response_time=rag_time,
            llm_response_time=llm_time,
            rag_has_citations=rag_citations,
            rag_word_count=rag_words,
            llm_word_count=llm_words,
            rag_specificity_score=rag_specificity,
            llm_specificity_score=llm_specificity
        )

    def print_detailed_results(self, result: ComparisonResult):
        """Print detailed comparison for a single result."""
        print(f"\n{'='*80}")
        print(f"DETAILED COMPARISON: {result.category}")
        print(f"{'='*80}")
        print(f"Question: {result.question}")
        print()

        print("🔬 RAG SYSTEM ANSWER:")
        print("-" * 40)
        print(result.rag_answer)
        print()

        print("🤖 DIRECT LLM ANSWER:")
        print("-" * 40)
        print(result.llm_answer)
        print()

        print("📊 METRICS COMPARISON:")
        print("-" * 40)
        print(f"Response Time:     RAG: {result.rag_response_time:.2f}s  |  LLM: {result.llm_response_time:.2f}s")
        print(f"Word Count:        RAG: {result.rag_word_count}         |  LLM: {result.llm_word_count}")
        print(f"Has Citations:     RAG: {'✅' if result.rag_has_citations else '❌'}            |  LLM: ❌")
        print(f"Specificity Score: RAG: {result.rag_specificity_score:.2f}        |  LLM: {result.llm_specificity_score:.2f}")

    def generate_summary_metrics(self):
        """Generate overall summary metrics."""
        if not self.results:
            return

        print(f"\n{'='*80}")
        print("SUMMARY METRICS")
        print(f"{'='*80}")

        # Category breakdown
        categories = {}
        for result in self.results:
            cat = result.category
            if cat not in categories:
                categories[cat] = {'count': 0, 'rag_citations': 0, 'avg_rag_specificity': 0, 'avg_llm_specificity': 0}

            categories[cat]['count'] += 1
            categories[cat]['rag_citations'] += 1 if result.rag_has_citations else 0
            categories[cat]['avg_rag_specificity'] += result.rag_specificity_score
            categories[cat]['avg_llm_specificity'] += result.llm_specificity_score

        # Calculate averages
        for cat, data in categories.items():
            data['avg_rag_specificity'] /= data['count']
            data['avg_llm_specificity'] /= data['count']
            data['citation_rate'] = data['rag_citations'] / data['count']

        print("\n📊 PERFORMANCE BY CATEGORY:")
        print("-" * 50)
        for cat, data in categories.items():
            print(f"\n{cat}:")
            print(f"  Tests: {data['count']}")
            print(f"  RAG Citation Rate: {data['citation_rate']:.1%}")
            print(f"  Avg Specificity - RAG: {data['avg_rag_specificity']:.2f} | LLM: {data['avg_llm_specificity']:.2f}")

        # Overall metrics
        total_tests = len(self.results)
        rag_citation_rate = sum(1 for r in self.results if r.rag_has_citations) / total_tests
        avg_rag_time = sum(r.rag_response_time for r in self.results) / total_tests
        avg_llm_time = sum(r.llm_response_time for r in self.results) / total_tests
        avg_rag_specificity = sum(r.rag_specificity_score for r in self.results) / total_tests
        avg_llm_specificity = sum(r.llm_specificity_score for r in self.results) / total_tests

        print("\n📈 OVERALL METRICS:")
        print("-" * 30)
        print(f"Total Tests: {total_tests}")
        print(f"RAG Citation Rate: {rag_citation_rate:.1%}")
        print(f"Avg Response Time - RAG: {avg_rag_time:.2f}s | LLM: {avg_llm_time:.2f}s")
        print(f"Avg Specificity - RAG: {avg_rag_specificity:.2f} | LLM: {avg_llm_specificity:.2f}")

        # Quality assessment
        print("\n🎯 QUALITY ASSESSMENT:")
        print("-" * 30)
        covered_research = [r for r in self.results if r.category == "Covered by PMC Research"]
        not_covered = [r for r in self.results if r.category == "Not in Current Research"]

        if covered_research:
            covered_citation_rate = sum(1 for r in covered_research if r.rag_has_citations) / len(covered_research)
            print(f"RAG citation rate on covered topics: {covered_citation_rate:.1%} (should be high)")

        if not_covered:
            not_covered_honesty = sum(1 for r in not_covered if "don't" in r.rag_answer.lower() or "no" in r.rag_answer.lower() or "cannot" in r.rag_answer.lower()) / len(not_covered)
            print(f"RAG honesty rate on uncovered topics: {not_covered_honesty:.1%} (should be high)")

    def run_full_test_suite(self, show_detailed: bool = True):
        """Run the complete test suite."""
        print("🧪 Starting RAG vs Direct LLM Test Suite")
        print(f"Testing {len(TEST_QUESTIONS)} questions across different categories")

        start_time = time.time()

        for i, question in enumerate(TEST_QUESTIONS, 1):
            print(f"\n[{i}/{len(TEST_QUESTIONS)}] {question.description}")
            result = self.run_comparison(question)
            self.results.append(result)

            if show_detailed:
                self.print_detailed_results(result)

        total_time = time.time() - start_time

        # Generate summary
        self.generate_summary_metrics()

        print(f"\n{'='*80}")
        print(f"🎉 TEST SUITE COMPLETED in {total_time:.2f} seconds")
        print(f"{'='*80}")


def main():
    """Main function to run the test suite."""
    import argparse

    parser = argparse.ArgumentParser(description='RAG vs LLM Test Suite')
    parser.add_argument('--quick', action='store_true', help='Run without detailed output')
    args = parser.parse_args()

    tester = RAGvsLLMTester()
    tester.run_full_test_suite(show_detailed=not args.quick)


if __name__ == "__main__":
    main()
