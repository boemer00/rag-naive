# RAG System Testing Strategy

## 🎯 Overview

This document outlines the comprehensive testing strategy for our RAG (Retrieval-Augmented Generation) system, following AI/MLOps best practices for model testing, quality gates, and continuous integration.

## 📁 Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Pytest configuration and fixtures
├── unit/                       # Unit tests (fast, isolated)
│   └── test_pmc_source.py     # PMC source component tests
├── integration/                # Integration tests (medium speed)
│   └── test_end_to_end.py     # End-to-end pipeline tests
└── performance/                # Performance tests (slow, comprehensive)
    ├── test_rag_vs_llm.py     # RAG vs LLM comparison suite
    └── test_quality_gates.py   # Quality gates and regression detection
```

## 🧪 Test Categories

### 1. Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Speed**: Fast (< 1s per test)
- **Scope**: Individual functions, classes, and modules
- **Examples**:
  - PMC source filtering logic
  - Paper metadata handling
  - Database operations

```bash
# Run unit tests
pytest tests/unit/ -v
```

### 2. Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions and end-to-end workflows
- **Speed**: Medium (1-10s per test)
- **Scope**: Complete pipelines and system interactions
- **Examples**:
  - Document loading and processing
  - Vector index creation
  - Question answering pipeline

```bash
# Run integration tests
pytest tests/integration/ -v
```

### 3. Performance Tests (`tests/performance/`)
- **Purpose**: Evaluate system performance and quality
- **Speed**: Slow (10s-5min per test)
- **Scope**: Model performance, response quality, and benchmarking
- **Examples**:
  - RAG vs Direct LLM comparisons
  - Response quality metrics
  - Performance regression detection

```bash
# Run performance tests
pytest tests/performance/ -v
```

## 🚨 Quality Gates

Quality gates define minimum acceptable performance thresholds that must be met for deployment:

### Defined Thresholds

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Citation Rate (Covered Topics) | ≥ 90% | RAG must cite sources for topics in corpus |
| Honesty Rate (Uncovered Topics) | ≥ 80% | RAG must acknowledge knowledge gaps |
| Specificity Ratio (RAG/LLM) | ≥ 1.0 | RAG should be more technical than generic LLM |
| Max Response Time | ≤ 15s | Maximum acceptable response time |
| Overall Specificity | ≥ 5.0 | Minimum technical depth score |

### Running Quality Gates

```bash
# Run quality gates (required for deployment)
pytest tests/performance/test_quality_gates.py::test_quality_gates -v

# Check for performance regression
pytest tests/performance/test_quality_gates.py::test_regression_detection -v
```

## 🔄 CI/CD Integration

### Automated Testing Pipeline

The system runs automatically on:
- **Push to main/develop**: Full test suite + quality gates
- **Pull requests**: Full test suite + quality gates + PR comment with results
- **Daily schedule**: Regression detection to catch data drift

### GitHub Actions Workflow

```yaml
# .github/workflows/rag-quality-gates.yml
- Unit tests (always run)
- Integration tests (requires OpenAI API key)
- Quality gates (fails build if not met)
- Regression detection (warns but doesn't fail)
- PR comments with detailed metrics
```

### Pre-commit Hooks

```bash
# Setup pre-commit hook (runs quality gates before commit)
make pre-commit-setup

# Manual pre-commit check
./scripts/pre-commit-quality-check.sh
```

## 📊 Performance Metrics

### Tracked Metrics

1. **Citation Rate**: Percentage of responses with research citations
2. **Honesty Rate**: Percentage of honest "I don't know" responses for uncovered topics
3. **Specificity Score**: Technical depth based on terminology and data points
4. **Response Time**: Time to generate answers
5. **Regression Detection**: Comparison with baseline performance

### Metric Interpretation

- **High Citation Rate on Covered Topics**: Indicates RAG successfully leverages research corpus
- **High Honesty Rate on Uncovered Topics**: Shows responsible AI behavior, prevents hallucination
- **Higher Specificity than Generic LLM**: Demonstrates value of research-backed responses
- **Consistent Response Times**: Ensures production viability

## 🛠 Development Workflow

### Local Development

```bash
# Quick development cycle
make dev-test        # Unit tests + quality gates

# Full development cycle  
make dev-full        # All tests + regression check

# Individual test types
make test-unit       # Unit tests only
make test-integration # Integration tests only
make quality-gates   # Quality gates only
```

### Before Committing

```bash
# Option 1: Use pre-commit hook (automatic)
git commit -m "Your changes"

# Option 2: Manual check
make full-check
git commit -m "Your changes"

# Option 3: Skip checks (emergency only)
git commit --no-verify -m "Emergency fix"
```

### When Quality Gates Fail

If quality gates fail, you have several options:

1. **Fix the Issue** (Recommended)
   - Review failed metrics in `test_results.json`
   - Identify root cause (data quality, model changes, etc.)
   - Implement fixes and re-test

2. **Adjust Thresholds** (Careful consideration required)
   - If consistently failing due to changed requirements
   - Update thresholds in `tests/performance/test_quality_gates.py`
   - Document rationale for changes

3. **Skip Temporarily** (Emergency only)
   ```bash
   git commit --no-verify -m "Emergency fix - bypass quality gates"
   ```

## 📈 Performance Regression Detection

### Baseline Management

- **Baseline Creation**: First successful run creates `baseline_performance.json`
- **Baseline Updates**: Automatically updated on successful main branch merges
- **Regression Threshold**: 10% decrease in key metrics triggers warning

### Handling Regressions

1. **Investigate Root Cause**
   - Data changes (new papers, different sources)
   - Model updates (OpenAI API changes)
   - Code changes affecting performance

2. **Response Options**
   - Fix underlying issue
   - Accept regression if justified (document rationale)
   - Update baseline if performance change is intentional

## 🎯 Best Practices

### For AI/ML Systems

1. **Automated Testing**: All changes go through automated quality checks
2. **Quality Gates**: Define and enforce minimum performance standards
3. **Regression Detection**: Catch performance degradation early
4. **Baseline Management**: Track performance over time
5. **Multiple Test Types**: Unit, integration, and performance tests

### For RAG Systems Specifically

1. **Citation Validation**: Ensure research-backed responses
2. **Honesty Metrics**: Prevent overconfident responses on unknown topics
3. **Specificity Measurement**: Validate technical depth of responses
4. **Response Time Monitoring**: Ensure production viability
5. **Comparative Analysis**: RAG vs baseline LLM performance

### When to Run Tests

- **Every commit**: Unit tests (via pre-commit hook)
- **Every PR**: Full test suite including quality gates
- **Daily**: Regression detection for data drift
- **Before deployment**: Full test suite must pass
- **After major changes**: Comprehensive performance evaluation

## 🚀 Quick Start

```bash
# 1. Install dependencies
make install

# 2. Setup pre-commit hook
make pre-commit-setup

# 3. Run full test suite
make full-check

# 4. If all passes, you're ready to develop!
```

This testing strategy ensures our RAG system maintains high quality, prevents regressions, and follows industry best practices for AI/ML system development.