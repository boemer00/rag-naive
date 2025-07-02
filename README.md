# RAG-Naive

A minimal, self-contained Retrieval-Augmented Generation (RAG) pipeline built with **LangChain**, **OpenAI**, and **Chroma**. It ingests a PDF, stores chunk embeddings locally, and answers questions via a simple CLI.

---

## Features
* End-to-end RAG workflow: PDF loading → text splitting → vector index → LLM QA chain
* Local persistent index for instant reuse (stored in `db/` by default)
* One-command setup and querying:
  ```bash
  python main.py 'What are the key findings or results presented in the paper?'
  ```
* Easily extensible—add more documents, change models, or swap components.

---

## Project Structure
```text
rag-naive/
├── raw_data/               # Source documents (PDFs, etc.)
├── src/
│   ├── loaders.py          # PDF loader
│   ├── splitters.py        # Text splitter
│   ├── indexer.py          # Build/load Chroma vector store
│   └── query.py            # Prompt + LLM helpers
├── main.py                 # Entry-point script
├── config.py               # Environment variable handling
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## Prerequisites
* Python **3.12** or newer
* A valid **OpenAI API key**

> 💡 The pipeline defaults to model `gpt-4.1-nano-2025-04-14`. Feel free to replace this with the OpenAI model of your choice in `config.py`.

---

## Installation
# Using **pyenv** + **pyenv-virtualenv** (recommended)
```bash
git clone https://github.com/your-org/rag-naive.git
cd rag-naive

# Install the exact Python version (if not already available)
pyenv install 3.12.3   # or any 3.9+ version you prefer

# Create and activate a dedicated virtualenv
pyenv virtualenv 3.12.3 rag-naive-env
pyenv local rag-naive-env  # sets .python-version for this project

pip install -r requirements.txt
```

---

## Environment Variables
Create a `.env` file in the project root (an example `.env.example` is provided):

```env
OPENAI_API_KEY=sk-...
# Optional: override where the Chroma DB is stored
PERSIST_DIRECTORY=db
```

Load variables automatically via `python-dotenv` on startup.

---

## One-Time Index Build
The first run will automatically build the vector index if `db/` is missing.
To force a rebuild later, delete `db/` or pass the `--reindex` flag (coming soon):

```bash
python main.py --reindex
```

---

## Asking Questions
```bash
python main.py "What are the key findings of the paper?"
```
The script will:
1. Ensure the index exists (building it if necessary).
2. Retrieve top-k relevant chunks.
3. Pass context + question to the LLM.
4. Print the answer.

---

## How It Works
1. **Loaders** – `PyPDFLoader` reads the PDF(s) in `raw_data/`.
2. **Splitters** – `RecursiveCharacterTextSplitter` chunks each document (default 1000 chars with 200 overlap).
3. **Indexer** – Each chunk is embedded via `text-embedding-3-small` and stored in a **Chroma** collection persisted locally.
4. **Query Pipeline** – A LangChain Expression (LCEL) chain retrieves the most similar chunks, injects them into a prompt, and calls the Chat model to generate an answer.

---

## Troubleshooting
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `OPENAI_API_KEY not set` | Missing `.env` | Add your key and restart |
| `TypeError: got multiple values for keyword argument 'embedding_function'` | Chroma bug when passing `embedding_function` twice | Use latest `master` (fixed in `src/indexer.py`) |
| Blank answer / "I don't know" | No relevant chunks retrieved | Add more documents or increase `k` in `main.py` |

---

## License
[MIT](LICENSE)
