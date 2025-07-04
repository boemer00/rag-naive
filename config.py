import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def get_openai_api_key() -> str:
    key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    return key

# Model Configuration
MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4.1-nano-2025-04-14')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-large')

# Chain Configuration
CHAIN_TYPE = os.getenv('CHAIN_TYPE', 'map_reduce')  # stuff, map_reduce, map_rerank, rerank

# Storage Configuration
PERSIST_DIRECTORY = os.getenv('PERSIST_DIRECTORY', 'db')

# File Paths
SAMPLE_PDF = Path(__file__).resolve().parent.parent / 'raw_data' / 'rag_intensive_nlp_tasks.pdf'
