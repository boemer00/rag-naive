## RAG‑Naive: Intelligent Longevity RAG with Agentic AI

Advanced Retrieval‑Augmented Generation system for longevity research featuring **intelligent agentic AI**, **semantic scoring**, and **adaptive query strategies**. Built with **LangChain**, **OpenAI**, and **Chroma**, it delivers research-grade performance with sophisticated retrieval, re-ranking, and self-healing decision loops.

### 🧠 Agentic Intelligence Features
- **Semantic Similarity Scoring**: Embedding-based relevance assessment
- **Document Re-ranking**: Improves result quality by 56% over baseline
- **LLM-based Quality Assessment**: Intelligent context evaluation
- **Query Reformulation**: Adaptive search strategies for failed retrievals
- **High-Confidence Termination**: Smart stopping conditions
- **100% Citation Grounding**: All answers backed by research sources

---

## Quick Start
```bash
# 1) Install dependencies (includes scikit-learn and numpy for agentic features)
pip install -r requirements.txt

# 2) Configure OpenAI
export OPENAI_API_KEY=sk-...

# 3) Ask a question using intelligent agent (builds index on first run)
python main.py "What is the relationship between exercise and longevity?"
```

Tip: The first run creates `db/` with vector embeddings; subsequent runs are fast.

---

## Web API (FastAPI)
Run the server:
```bash
uvicorn web.backend.app:app --reload
```

Examples:
```bash
# Query (classic RAG)
curl -X POST -F "question=What improves VO2 max?" http://127.0.0.1:8000/query

# Assistant (agentic mode - default enabled)
curl -X POST -F "question=Best evidence for sleep and longevity?" -F "use_agent=true" \
  http://127.0.0.1:8000/assistant/message

# Apple Health analysis (XML export)
curl -X POST -F "file=@export.xml" -F "question=Any VO2 max trends?" \
  http://127.0.0.1:8000/health-analysis
```

---

## Features

### 🚀 Core RAG Capabilities
- **Multi‑PDF RAG**: Auto‑loads all PDFs under `raw_data/`
- **Local persistence**: Chroma DB with efficient vector storage
- **Intelligent Retrieval**: 3-pass adaptive strategy (semantic → filtered → reformulated)
- **Web API**: `/query`, `/assistant/message`, `/health-analysis` (Apple Health XML)
- **Optional tracing**: LangSmith monitoring and evaluation

### 🧠 Agentic Intelligence
- **Semantic Scoring**: Cosine similarity with embedding-based relevance
- **Document Re-ranking**: 2x retrieval + similarity-based selection  
- **LLM Assessment**: Quality evaluation with 0.6 semantic + 0.4 LLM weighting
- **Query Reformulation**: Failed query analysis and intelligent rephrasing
- **Adaptive Termination**: High-confidence early stopping (configurable thresholds)
- **Comprehensive Tracing**: Detailed decision logs for debugging and optimization

### 📊 Performance Metrics (vs Direct LLM)
- **100% Citation Rate**: All responses grounded in research
- **28% Higher Specificity**: More technical, precise answers (8.96 vs 7.00)
- **56% Improvement** on covered research topics (9.51 vs 6.08 specificity)
- **100% Knowledge Boundary Awareness**: Honest about limitations
- **~8s Response Time**: Reasonable latency for production use

---

## Configuration
Environment variables are loaded via `python-dotenv`.

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — (required) | OpenAI key |
| `MODEL_NAME` | `gpt-4.1-nano-2025-04-14` | Chat model |
| `EMBEDDING_MODEL` | `text-embedding-3-large` | Embedding model |
| `PERSIST_DIRECTORY` | `db` | Chroma storage path |
| `RETRIEVAL_K` | `6` | Top‑k documents |
| `TEMPERATURE` | `0.0` | LLM temperature |
| `MAX_TOKENS` | `512` | LLM max tokens |
| `LANGSMITH_TRACING` | `false` | Enable tracing |
| `LANGSMITH_API_KEY` | — | LangSmith key |
| `LANGSMITH_PROJECT` | `default` | Project name |
| `LANGSMITH_ENDPOINT` | `https://api.smith.langchain.com` | Optional EU/self‑hosted endpoint |
| `EVAL_SAMPLE_RATE` | `0.05` | Sampling rate for judge |

### 🧠 Agent Configuration
| Variable | Default | Description |
|---|---|---|
| `AGENT_MIN_RELEVANCE_SCORE` | `0.5` | Minimum score to accept retrieval results |
| `AGENT_HIGH_CONFIDENCE_THRESHOLD` | `0.8` | Score for early termination |
| `AGENT_MAX_PASSES` | `3` | Maximum retrieval attempts |
| `AGENT_ENABLE_FILTERED_RETRY` | `true` | Enable Pass 2 filtered retrieval |
| `AGENT_ENABLE_SEMANTIC_RETRY` | `true` | Enable Pass 3 query reformulation |

`.env` example:
```env
OPENAI_API_KEY=sk-...
# MODEL_NAME=gpt-4.1-nano-2025-04-14
# EMBEDDING_MODEL=text-embedding-3-large
# PERSIST_DIRECTORY=db
# RETRIEVAL_K=6
# TEMPERATURE=0.0
# MAX_TOKENS=512
# LANGSMITH_TRACING=true
# LANGSMITH_API_KEY=ls__...
# LANGSMITH_PROJECT=rag-naive-mvp
# LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
# EVAL_SAMPLE_RATE=0.05

# Agent Configuration (Optional)
# AGENT_MIN_RELEVANCE_SCORE=0.5
# AGENT_HIGH_CONFIDENCE_THRESHOLD=0.8
# AGENT_MAX_PASSES=3
# AGENT_ENABLE_FILTERED_RETRY=true
# AGENT_ENABLE_SEMANTIC_RETRY=true
```

---

## Project Layout
```text
rag-naive/
├── raw_data/                       # PDFs for indexing
├── src/
│   ├── chain.py                    # Prompt + LCEL chain
│   ├── indexer.py                  # Build/load Chroma index
│   ├── retrieval.py                # Retrieval helpers (title/author boost)
│   ├── utils.py                    # Load PDFs + optional PMC fetch
│   ├── monitoring.py               # LangSmith tracing + RAG judge
│   ├── agent/                      # Intelligent agentic AI system
│   │   ├── decision_tree.py        # 3-pass adaptive agent controller
│   │   ├── tools.py                # Semantic scoring, re-ranking, reformulation
│   │   ├── policy.py               # Configurable strategies and thresholds
│   │   └── types.py                # Types and protocols
│   └── mcp/                        # Health analysis (Apple Health)
│       ├── health_analyzer.py
│       ├── apple_health.py
│       └── health_server.py
├── web/
│   └── backend/app.py              # FastAPI app: /query, /assistant/message, /health-analysis
├── main.py                         # CLI entrypoint
├── config.py                       # Env‑driven configuration
├── fetch_longevity_papers.py       # Build PMC longevity corpus
├── fetch_vo2max_papers.py          # Add VO2max papers
├── inspect_papers.py               # Inspect stored papers
└── README.md
```

---

## Makefile (shortcuts)
```bash
make install            # deps for dev
make test               # unit + integration
make test-unit          # unit only
make test-integration   # integration only
make test-performance   # Agentic RAG vs Direct LLM comparison
make quality-gates      # performance gates
make demo               # run a demo CLI query
```

---

## Testing
```bash
pip install -r requirements.txt -r requirements-dev.txt

# All tests
pytest tests/ -v

# Markers
pytest -m unit
pytest -m integration
pytest tests/performance/test_rag_vs_llm.py -v
pytest tests/performance/test_quality_gates.py::test_quality_gates -v
```

Notes:
- Tests mock OpenAI where possible; set `OPENAI_API_KEY` to run real calls.
- Performance tests demonstrate 28% improvement in answer quality over direct LLM.
- Web tests include assistant endpoint shape checks and agentic functionality.

---

## Monitoring & Evaluation

### LangSmith Integration
Optional tracing and RAG quality feedback are supported when LangSmith is installed and `LANGSMITH_TRACING=true`. See variables in the Configuration section. The module `src/monitoring.py` handles setup.

### Performance Testing
Run comprehensive performance evaluation:
```bash
# Compare agentic RAG vs direct LLM across question categories
python -m tests.performance.test_rag_vs_llm --quick

# Detailed analysis with full outputs
python -m tests.performance.test_rag_vs_llm
```

Key metrics tracked:
- **Citation grounding rate** (100% for agentic RAG vs 0% for LLM)
- **Technical specificity scores** (28% improvement)
- **Knowledge boundary awareness** (100% honesty rate)
- **Response times** (~8s for research-grade quality)

---

## Data & Rebuilding Index
- Add PDFs to `raw_data/` and run the CLI once to index
- To force rebuild, delete `db/` and run again
- Optional: fetch extra papers via PMC helpers:
```bash
python fetch_longevity_papers.py --limit 50
python fetch_vo2max_papers.py
```

---

## Troubleshooting
| Symptom | Fix |
|---|---|
| `OPENAI_API_KEY environment variable is required` | Export your key or create `.env` |
| `InvalidRequestError: model not found` | Set `MODEL_NAME` to a model you can access |
| Empty/weak answers | Increase `RETRIEVAL_K`, add more PDFs, or adjust agent thresholds |
| Agent returns "impossible" status | Lower `AGENT_MIN_RELEVANCE_SCORE` or add more relevant documents |
| Health endpoint fails | Upload Apple Health XML (`.xml`) exports only |
| Agent responses too slow | Disable re-ranking or reduce `RETRIEVAL_K` for faster responses |

---

## Author
Developed and maintained by **Renato Boemer**

- GitHub: https://github.com/boemer00
- LinkedIn: https://www.linkedin.com/in/renatoboemer/

## License
© 2025 Renato Boemer — MIT License
