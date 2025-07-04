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

Create a `.env` file:
```env
OPENAI_API_KEY=sk-...
# Optional overrides:
# MODEL_NAME=gpt-3.5-turbo
# PERSIST_DIRECTORY=my_db
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

## License
MIT
