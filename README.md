# RAG-Naive

A minimal, self-contained Retrieval-Augmented Generation (RAG) pipeline built with **LangChain**, **OpenAI**, and **Chroma**.
It ingests a PDF, stores chunk embeddings locally, and answers questions from the command line in one step.

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
python main.py "What are the key findings presented in the paper?"
```

> The first invocation builds a vector index under `db/`. Subsequent runs reuse it and answer instantly.

---

## Features
* End-to-end RAG flow: **PDF loader → chunk splitter → Chroma vector store → LLM answer**
* Persistent local index for offline reuse (`db/` directory)
* Smart metadata boosting – questions about *title* or *author* are answered more reliably
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
├── raw_data/               # Source documents (PDFs, etc.)
│   └── rag_intensive_nlp_tasks.pdf
├── src/
│   ├── loaders.py          # PDF → Document objects
│   ├── splitters.py        # Chunking & section tagging
│   ├── indexer.py          # Build/load Chroma DB
│   ├── retrieval.py        # Metadata-aware retrieval helper
│   ├── utils.py            # Convenience loader for default PDF
│   └── chain.py            # Prompt & LCEL chain factory
├── main.py                 # CLI entry point
├── config.py               # Env-driven configuration
├── requirements.txt        # Locked dependencies
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

Create a `.env` file:
```env
OPENAI_API_KEY=sk-...
# MODEL_NAME=gpt-4.1-nano-2025-04-14
# PERSIST_DIRECTORY=my_db
# LANGSMITH_TRACING=true
# LANGSMITH_API_KEY=ls__org_...
# LANGSMITH_PROJECT=rag-naive-mvp
# LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
```

---

## How It Works (Technical Walk-Through)
1. **Loading** – `PyPDFLoader` reads each PDF into `langchain.schema.Document` objects.
2. **Splitting** – `RecursiveCharacterTextSplitter` chunks text (~1000 chars with 200 overlap) and tags sections (Introduction, Methods, …).
3. **Embedding & Storage** – Each chunk is embedded via `OpenAIEmbeddings` (`text-embedding-3-large`) and stored in a local **Chroma** collection.
4. **Retrieval** – On a query, the top-k semantically similar chunks are fetched.
   If the question references *title* or *author*, page-0 chunks are boosted.
5. **Generation** – Chunks are injected into a carefully crafted prompt and answered by the chat model.

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
- ✅ Python 3.11 setup with dependency caching
- ✅ Installation of all requirements
- ✅ Execution of the complete test suite
- ✅ Failure blocking for broken commits

The CI pipeline works both with and without OpenAI API keys, using intelligent mocking when needed.

---

## Extending
* **Multiple PDFs** – Loop through `raw_data/` in `utils.load_source_docs`.
* **Different splitter** – Swap `RecursiveCharacterTextSplitter` for `TokenTextSplitter`.
* **Alternate LLM** – Set `MODEL_NAME` to any model supported by `langchain_openai.ChatOpenAI`.

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
