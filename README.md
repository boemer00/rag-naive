# RAG-Naive

A minimal, self-contained Retrieval-Augmented Generation (RAG) pipeline built with **LangChain**, **OpenAI**, and **Chroma**.
It ingests multiple research papers, stores chunk embeddings locally with rich metadata, and answers questions from the command line in one step.

---

## Quick Start
```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Export your OpenAI key
export OPENAI_API_KEY=sk-...

#    # (Optional) Enable LangSmith tracing – set these env vars or see the
#    # "Monitoring & Observability" section below
#    # LANGSMITH_TRACING=true
#    # LANGSMITH_API_KEY=ls__...
#    # LANGSMITH_PROJECT=rag-naive-mvp

# 3. Ask a question (index builds automatically on first run)
python main.py "What is the relationship between exercise and longevity?"
```

> The first invocation builds a vector index under `db/`. Subsequent runs reuse it and answer instantly.

---

## Features
* **Multi-document RAG**: Processes multiple research papers from `raw_data/` directory automatically
* **Rich metadata extraction**: Automatically detects study types, research topics, and biomarkers
* **Smart filtering**: Topic-based and study-type filtering for precision retrieval
* **Longevity-focused**: Pre-configured for longevity research with cardiovascular, exercise, nutrition topics
* End-to-end RAG flow: **Multi-PDF loader → enriched chunking → Chroma vector store → LLM answer**
* Persistent local index for offline reuse (`db/` directory)
* **Backward compatible**: Still supports single PDF mode for existing workflows
* Zero configuration beyond `OPENAI_API_KEY`
* **Optional LangSmith monitoring** – one export away from live traces & dashboards

---

## Monitoring & Observability (LangSmith)

Want rich traces and latency / token-cost dashboards?

1. Install the extra SDK (already pinned in `requirements.txt`, but explicit here):

   ```bash
   pip install langsmith
   ```

2. Export the required variables (US region example):

   ```bash
   export LANGSMITH_TRACING=true
   export LANGSMITH_API_KEY=ls__org_...   # or ls__proj_...
   export LANGSMITH_PROJECT=rag-naive-mvp
   ```

   European data residency:

   ```bash
   export LANGSMITH_ENDPOINT="https://eu.api.smith.langchain.com"
   ```

3. Run the app – traces appear instantly at <https://smith.langchain.com> under your chosen project.

That’s it! The `src/monitoring.py` module auto-configures everything at start-up.

---

## Project Layout
```text
rag-naive/
├── raw_data/               # Source documents (multiple PDFs supported)
│   ├── Longevity leap-mind the healthspan gap.pdf
│   ├── Benonisdottir_et_al_2024_Genetics_of_female.pdf  
│   ├── Implausibility of radical life extension in humans...pdf
│   └── Towards AI-driven longevity research an overview.pdf
├── src/
│   ├── loaders.py          # PDF → Document objects
│   ├── splitters.py        # Chunking, section tagging & metadata extraction
│   ├── indexer.py          # Build/load Chroma DB
│   ├── retrieval.py        # Metadata-aware retrieval helper
│   ├── utils.py            # Multi-document loader with paper metadata
│   ├── monitoring.py       # LangSmith tracing & RAG metrics
│   └── chain.py            # Prompt & LCEL chain factory
├── main.py                 # CLI entry point
├── config.py               # Env-driven configuration
├── requirements.txt        # Locked dependencies
├── demo_multidoc.py        # Multi-document RAG demonstration
├── compare_answers.py      # RAG vs direct LLM comparison
└── README.md               # You are here
```

---

## Configuration
All runtime options are controlled via environment variables (loaded automatically with `python-dotenv`):

| Variable            | Default                         | Description                              |
|---------------------|---------------------------------|------------------------------------------|
| `OPENAI_API_KEY`    | — (required)                    | Your OpenAI secret key                   |
| `MODEL_NAME`        | `gpt-4.1-nano-2025-04-14`       | Chat model used for answers              |
| `EMBEDDING_MODEL`   | `text-embedding-3-large`        | Model used to embed chunks               |
| `PERSIST_DIRECTORY` | `db`                            | Folder to store the Chroma collection    |
| `CHAIN_TYPE`        | `map_reduce`                    | LLM chaining strategy (future feature)   |
| `LANGSMITH_TRACING` | `false`                         | Toggle LangSmith tracing                 |
| `LANGSMITH_API_KEY` | —                               | Personal or project API key              |
| `LANGSMITH_PROJECT` | `default`                       | Project name to group traces             |
| `LANGSMITH_ENDPOINT`| `https://api.smith.langchain.com` | Override for EU/self-hosted region       |
| `EVAL_SAMPLE_RATE`  | `0.05`                           | Sampling rate for RAG evaluation metrics |

Create a `.env` file:
```env
OPENAI_API_KEY=sk-...
# MODEL_NAME=gpt-4.1-nano-2025-04-14
# PERSIST_DIRECTORY=my_db
# LANGSMITH_TRACING=true
# LANGSMITH_API_KEY=ls__org_...
# LANGSMITH_PROJECT=rag-naive-mvp
# LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
# EVAL_SAMPLE_RATE=0.05
```

---

## How It Works (Technical Walk-Through)
1. **Multi-Document Loading** – `PyPDFLoader` reads all PDFs from `raw_data/` into `langchain.schema.Document` objects with paper-level metadata.
2. **Enhanced Splitting** – `RecursiveCharacterTextSplitter` chunks text (~1000 chars with 200 overlap) and enriches with:
   - Section tagging (Introduction, Methods, Results, etc.)
   - Study type detection (meta-analysis, RCT, observational)
   - Topic classification (cardiovascular, exercise, nutrition, longevity)
   - Biomarker identification (heart_rate, blood_pressure, sleep_metrics)
3. **Embedding & Storage** – Each enriched chunk is embedded via `OpenAIEmbeddings` (`text-embedding-3-large`) and stored in a unified **Chroma** collection.
4. **Smart Retrieval** – On a query, semantically similar chunks are fetched with metadata boosting for:
   - Topic relevance (cardiovascular queries prioritize cardiovascular chunks)
   - Study quality (meta-analyses and RCTs get higher priority)
   - Title/author references (page-0 chunks are boosted)
5. **Research-Grounded Generation** – Retrieved chunks are injected into a domain-expert prompt and answered by the chat model with proper citations.

---

## Rebuilding the Index
Delete the folder specified by `PERSIST_DIRECTORY` (default `db/`) and re-run `main.py`.
A CLI flag (`--reindex`) will be added soon – track progress in `issues/5`.

---

## Testing

This project includes automated tests to ensure the RAG pipeline works correctly.

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run only integration tests
pytest tests/ -v -m integration

# Run tests without the integration marker
pytest tests/ -v -m "not integration"
```

### Test Structure

- **`tests/test_smoke.py`** - Integration smoke test that validates the end-to-end RAG pipeline
  - Automatically mocks OpenAI API if no `OPENAI_API_KEY` is available
  - Verifies the pipeline can load documents, process questions, and generate responses
  - Tests with the question "What is RAG?" and validates response quality

### Continuous Integration

Every push and pull request triggers automated testing via GitHub Actions:
- ✅ Python 3.12 setup with dependency caching
- ✅ Installation of all requirements
- ✅ Execution of the complete test suite
- ✅ Failure blocking for broken commits

The CI pipeline works both with and without OpenAI API keys, using intelligent mocking when needed.

---

## Multi-Document Features

### Current Implementation
The system now automatically processes **multiple research papers** with rich metadata:

```bash
# View corpus analysis
python demo_multidoc.py

# Compare RAG vs direct LLM answers
python compare_answers.py
```

### Corpus Statistics
- **374 chunks** from **4 longevity research papers**
- **Smart metadata extraction**: study types, topics, biomarkers
- **Topic distribution**: longevity (231), cardiovascular (27), exercise (16), nutrition (12)
- **Study types**: meta-analysis (17), RCT (14), observational (14), general (329)

### Advanced Filtering
The metadata enables sophisticated retrieval patterns:
- **Topic filtering**: `cardiovascular` queries find 27 relevant chunks
- **Evidence filtering**: `meta-analysis` queries prioritize 17 high-quality chunks  
- **Biomarker filtering**: `heart_rate` queries target 125 relevant chunks

---

## Extending
* **Add more papers** – Drop PDFs into `raw_data/` directory and rebuild index
* **Custom metadata** – Extend topic/biomarker detection in `splitters.py`
* **Different splitter** – Swap `RecursiveCharacterTextSplitter` for `TokenTextSplitter`
* **Alternate LLM** – Set `MODEL_NAME` to any model supported by `langchain_openai.ChatOpenAI`
* **Advanced retrieval** – The metadata foundation supports topic collections, hierarchical RAG, and hybrid search

---

## Troubleshooting
| Symptom                                         | Fix |
|-------------------------------------------------|-----|
| `OPENAI_API_KEY environment variable is required` | Export your key or create `.env` |
| `InvalidRequestError: model not found`          | Change `MODEL_NAME` to one you have access to |
| No answer / “I don’t know”                      | Increase `k` in `main.answer()` or add more docs |

---

## Author
   Developed and maintained by **Renato Boemer**

   • GitHub: https://github.com/boemer00

   • LinkedIn: https://www.linkedin.com/in/renatoboemer/

   • [![Follow](https://img.shields.io/github/followers/boemer00?label=Follow%20%40boemer00&style=social)](https://github.com/boemer00)

---

## License
© 2025 Renato Boemer - MIT License
