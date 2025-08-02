#!/bin/bash
# Pre-commit hook for RAG quality checks
# Place this in .git/hooks/pre-commit to run automatically

set -e

echo "Running RAG Quality Checks..."

# Check if we have the required API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set. Skipping quality gates."
    echo "   Set the key to run full quality checks."
    exit 0
fi

# Run unit tests (fast)
echo "📝 Running unit tests..."
pytest tests/unit/ -v -q

# Run integration tests (medium speed)
echo "🔗 Running integration tests..."
pytest tests/integration/ -v -q

# Run quality gates (slow but critical)
echo "🚨 Running performance quality gates..."
if pytest tests/performance/test_quality_gates.py::test_quality_gates -v; then
    echo "✅ All quality gates passed!"
else
    echo "❌ Quality gates failed!"
    echo ""
    echo "💡 Options:"
    echo "   1. Fix the performance issues"
    echo "   2. Skip with: git commit --no-verify"
    echo "   3. Review failed metrics in test_results.json"
    exit 1
fi

# Check for regressions (warn only)
if pytest tests/performance/test_quality_gates.py::test_regression_detection -v; then
    echo "✅ No performance regression detected"
else
    echo "⚠️  Performance regression detected - review before merging"
fi

echo "🎉 All pre-commit checks passed!"
