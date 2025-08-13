"""
Performance quality gates for RAG system.
Defines minimum acceptable performance thresholds.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from .test_rag_vs_llm import TEST_QUESTIONS, RAGvsLLMTester


class QualityGates:
    """Define performance thresholds for RAG system."""

    # Minimum acceptable performance thresholds
    MIN_CITATION_RATE_COVERED = 0.90    # 90% for covered topics
    MIN_HONESTY_RATE_UNCOVERED = 0.80   # 80% for uncovered topics
    MIN_SPECIFICITY_RATIO = 1.0         # RAG should be >= LLM specificity
    MAX_RESPONSE_TIME = 15.0            # Max 15 seconds per response
    MIN_OVERALL_SPECIFICITY = 5.0       # Minimum technical depth
    MIN_FAITHFULNESS = 0.70             # Minimum average faithfulness

    @classmethod
    def check_all_gates(cls, results: list) -> tuple[bool, dict]:
        """
        Check all quality gates against test results.

        Returns:
            (passed: bool, metrics: dict)
        """
        if not results:
            return False, {"error": "No test results provided"}

        # Calculate metrics
        covered_results = [r for r in results if r.category == "Covered by PMC Research"]
        uncovered_results = [r for r in results if r.category == "Not in Current Research"]

        metrics = {
            "total_tests": len(results),
            "citation_rate_covered": 0.0,
            "honesty_rate_uncovered": 0.0,
            "avg_specificity_ratio": 0.0,
            "max_response_time": 0.0,
            "avg_rag_specificity": 0.0,
            "avg_rag_faithfulness": 0.0,
            "gates_passed": {},
            "gates_failed": {}
        }

        # Calculate citation rate for covered topics
        if covered_results:
            citation_rate = sum(1 for r in covered_results if r.rag_has_citations) / len(covered_results)
            metrics["citation_rate_covered"] = citation_rate

            if citation_rate >= cls.MIN_CITATION_RATE_COVERED:
                metrics["gates_passed"]["citation_rate"] = f"{citation_rate:.1%} >= {cls.MIN_CITATION_RATE_COVERED:.1%}"
            else:
                metrics["gates_failed"]["citation_rate"] = f"{citation_rate:.1%} < {cls.MIN_CITATION_RATE_COVERED:.1%}"

        # Calculate honesty rate for uncovered topics
        if uncovered_results:
            honesty_keywords = ["don't", "no", "cannot", "not available", "limitations", "consult"]
            honesty_rate = sum(1 for r in uncovered_results
                             if any(keyword in r.rag_answer.lower() for keyword in honesty_keywords)) / len(uncovered_results)
            metrics["honesty_rate_uncovered"] = honesty_rate

            if honesty_rate >= cls.MIN_HONESTY_RATE_UNCOVERED:
                metrics["gates_passed"]["honesty_rate"] = f"{honesty_rate:.1%} >= {cls.MIN_HONESTY_RATE_UNCOVERED:.1%}"
            else:
                metrics["gates_failed"]["honesty_rate"] = f"{honesty_rate:.1%} < {cls.MIN_HONESTY_RATE_UNCOVERED:.1%}"

        # Calculate specificity ratio (RAG vs LLM)
        specificity_ratios = [r.rag_specificity_score / max(r.llm_specificity_score, 0.1) for r in results]
        avg_ratio = sum(specificity_ratios) / len(specificity_ratios)
        metrics["avg_specificity_ratio"] = avg_ratio

        if avg_ratio >= cls.MIN_SPECIFICITY_RATIO:
            metrics["gates_passed"]["specificity_ratio"] = f"{avg_ratio:.2f} >= {cls.MIN_SPECIFICITY_RATIO:.2f}"
        else:
            metrics["gates_failed"]["specificity_ratio"] = f"{avg_ratio:.2f} < {cls.MIN_SPECIFICITY_RATIO:.2f}"

        # Check response time
        max_time = max(r.rag_response_time for r in results)
        metrics["max_response_time"] = max_time

        if max_time <= cls.MAX_RESPONSE_TIME:
            metrics["gates_passed"]["response_time"] = f"{max_time:.2f}s <= {cls.MAX_RESPONSE_TIME}s"
        else:
            metrics["gates_failed"]["response_time"] = f"{max_time:.2f}s > {cls.MAX_RESPONSE_TIME}s"

        # Check overall specificity
        avg_specificity = sum(r.rag_specificity_score for r in results) / len(results)
        metrics["avg_rag_specificity"] = avg_specificity

        if avg_specificity >= cls.MIN_OVERALL_SPECIFICITY:
            metrics["gates_passed"]["overall_specificity"] = f"{avg_specificity:.2f} >= {cls.MIN_OVERALL_SPECIFICITY}"
        else:
            metrics["gates_failed"]["overall_specificity"] = f"{avg_specificity:.2f} < {cls.MIN_OVERALL_SPECIFICITY}"

        # Check average faithfulness
        avg_faithfulness = sum(getattr(r, 'rag_faithfulness', 0.0) for r in results) / len(results)
        metrics["avg_rag_faithfulness"] = avg_faithfulness

        if avg_faithfulness >= cls.MIN_FAITHFULNESS:
            metrics["gates_passed"]["faithfulness"] = f"{avg_faithfulness:.2f} >= {cls.MIN_FAITHFULNESS}"
        else:
            metrics["gates_failed"]["faithfulness"] = f"{avg_faithfulness:.2f} < {cls.MIN_FAITHFULNESS}"

        # Overall pass/fail
        all_passed = len(metrics["gates_failed"]) == 0

        return all_passed, metrics


@pytest.mark.performance
@pytest.mark.timeout(300)  # 5 minute timeout
def test_quality_gates():
    """
    Main quality gate test that must pass for deployment.
    This test defines the minimum acceptable performance.
    """
    print("\n🚨 Running Quality Gates Test...")

    # Run the full test suite
    tester = RAGvsLLMTester()

    # Execute all test questions
    for question in TEST_QUESTIONS:
        result = tester.run_comparison(question)
        tester.results.append(result)

    # Check quality gates
    passed, metrics = QualityGates.check_all_gates(tester.results)

    # Save results for CI/CD
    results_file = Path("test_results.json")
    with open(results_file, "w") as f:
        json.dump({
            "passed": passed,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat(),
            "test_count": len(tester.results)
        }, f, indent=2)

    # Print detailed results
    print(f"\n{'='*60}")
    print("QUALITY GATES RESULTS")
    print(f"{'='*60}")

    print("\n✅ PASSED GATES:")
    for gate, value in metrics["gates_passed"].items():
        print(f"  {gate}: {value}")

    if metrics["gates_failed"]:
        print("\n❌ FAILED GATES:")
        for gate, value in metrics["gates_failed"].items():
            print(f"  {gate}: {value}")

    print(f"\nOVERALL RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")

    # Assert for pytest
    if not passed:
        pytest.fail(f"Quality gates failed. Failed gates: {list(metrics['gates_failed'].keys())}")

    print("🎉 All quality gates passed! System ready for deployment.")


def test_regression_detection():
    """
    Detect performance regression by comparing with baseline.
    This helps catch performance degradation over time.
    """
    baseline_file = Path("baseline_performance.json")
    current_results_file = Path("test_results.json")

    if not baseline_file.exists():
        pytest.skip("No baseline performance file found. Run test_quality_gates first to establish baseline.")

    if not current_results_file.exists():
        pytest.skip("No current test results found. Run test_quality_gates first.")

    # Load baseline and current results
    with open(baseline_file) as f:
        baseline = json.load(f)

    with open(current_results_file) as f:
        current = json.load(f)

    # Check for significant regression (>10% decrease in key metrics)
    regression_threshold = 0.10

    key_metrics = [
        "citation_rate_covered",
        "honesty_rate_uncovered",
        "avg_specificity_ratio",
        "avg_rag_specificity"
    ]

    regressions = []

    for metric in key_metrics:
        if metric in baseline["metrics"] and metric in current["metrics"]:
            baseline_val = baseline["metrics"][metric]
            current_val = current["metrics"][metric]

            if baseline_val > 0:  # Avoid division by zero
                change = (current_val - baseline_val) / baseline_val

                if change < -regression_threshold:  # Significant decrease
                    regressions.append({
                        "metric": metric,
                        "baseline": baseline_val,
                        "current": current_val,
                        "change": change
                    })

    if regressions:
        regression_msg = "\n".join([
            f"  {r['metric']}: {r['baseline']:.3f} → {r['current']:.3f} ({r['change']:.1%})"
            for r in regressions
        ])
        pytest.fail(f"Performance regression detected:\n{regression_msg}")

    print("✅ No significant performance regression detected.")


if __name__ == "__main__":
    # Allow running quality gates directly
    test_quality_gates()
    test_regression_detection()
