# Makefile for RAG system development and testing

.PHONY: help install test test-unit test-integration test-performance quality-gates lint format clean

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt -r requirements-dev.txt

test: test-unit test-integration  ## Run all tests except performance

test-unit:  ## Run unit tests only
	pytest tests/unit/ -v

test-integration:  ## Run integration tests only
	pytest tests/integration/ -v

test-performance:  ## Run performance comparison tests
	pytest tests/performance/test_rag_vs_llm.py -v --tb=short

quality-gates:  ## Run performance quality gates (critical for deployment)
	pytest tests/performance/test_quality_gates.py::test_quality_gates -v

regression-check:  ## Check for performance regression
	pytest tests/performance/test_quality_gates.py::test_regression_detection -v

full-check: test quality-gates regression-check  ## Run complete test suite

lint:  ## Run code linting
	ruff check .
	mypy src/

format:  ## Format code
	black .
	ruff check --fix .

pre-commit-setup:  ## Setup pre-commit hook
	cp scripts/pre-commit-quality-check.sh .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "✅ Pre-commit hook installed"

clean:  ## Clean temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f test_results.json
	rm -rf .pytest_cache/

fetch-papers:  ## Fetch longevity papers from PMC
	python fetch_longevity_papers.py --limit 10

inspect-papers:  ## Inspect stored research papers
	python inspect_papers.py

demo:  ## Run a demo query
	python main.py "What are the key factors for healthy aging?"

# Development shortcuts
dev-test: test-unit quality-gates  ## Quick development test cycle
dev-full: clean test quality-gates regression-check  ## Full development test cycle

# CI/CD simulation
ci-test:  ## Simulate CI/CD testing pipeline
	@echo "🔄 Simulating CI/CD pipeline..."
	$(MAKE) clean
	$(MAKE) install
	$(MAKE) test
	$(MAKE) quality-gates
	@echo "✅ CI/CD simulation completed successfully"