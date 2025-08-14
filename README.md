## RAG‑Naive: Longevity RAG + Agent PoC

Retrieval‑Augmented Generation pipeline for longevity research using **LangChain**, **OpenAI**, and **Chroma**. It ingests PDFs in `raw_data/`, builds a local vector index, and answers research questions via CLI or Web API. Includes a lightweight decision‑agent scaffold and optional Apple Health analysis endpoint.

---

## Quick Start
```bash
# 1) Install
pip install -r requirements.txt

# 2) Configure OpenAI
export OPENAI_API_KEY=sk-...

# 3) Ask a question (builds index on first run)
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

# Assistant (toggle agent)
curl -X POST -F "question=Best evidence for sleep and longevity?" -F "use_agent=true" \
  http://127.0.0.1:8000/assistant/message

# Apple Health analysis (XML export)
curl -X POST -F "file=@export.xml" -F "question=Any VO2 max trends?" \
  http://127.0.0.1:8000/health-analysis
```

---

## Features
- **Multi‑PDF RAG**: Auto‑loads all PDFs under `raw_data/`
- **Local persistence**: Chroma DB in `db/`
- **Simple smart retrieval**: Heuristics for title/author boosts and filtered retries
- **Agent PoC**: Decision‑tree scaffold with semantic and filtered retries
- **Web API**: `/query`, `/assistant/message` (optional agent), `/health-analysis` (Apple Health XML)
- **Optional tracing**: LangSmith sampling and feedback

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
│   ├── agent/                      # Decision agent scaffold
│   │   ├── decision_tree.py        # Agent controller (scaffold)
│   │   ├── tools.py                # Retrieval/answer tools (scaffold)
│   │   ├── policy.py               # Policy config
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
make test-performance   # RAG vs LLM comparison
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
- Web tests include an assistant endpoint shape check.

---

## Monitoring (LangSmith)
Optional tracing and RAG quality feedback are supported when LangSmith is installed and `LANGSMITH_TRACING=true`. See variables in the Configuration section. The module `src/monitoring.py` handles setup.

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
| Empty/weak answers | Increase `RETRIEVAL_K` or add more PDFs |
| Health endpoint fails | Upload Apple Health XML (`.xml`) exports only |

---

## Author
Developed and maintained by **Renato Boemer**

- GitHub: https://github.com/boemer00
- LinkedIn: https://www.linkedin.com/in/renatoboemer/

## License
© 2025 Renato Boemer — MIT License
