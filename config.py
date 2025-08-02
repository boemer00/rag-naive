import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class RAGConfig:
    """Centralized configuration for RAG pipeline with validation."""

    # API Configuration
    openai_api_key: str

    # Model Configuration
    model_name: str = 'gpt-4.1-nano-2025-04-14'
    embedding_model: str = 'text-embedding-3-large'

    # Retrieval Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_k: int = 6

    # Chain Configuration
    chain_type: str = 'map_reduce'
    temperature: float = 0.0
    max_tokens: int = 512

    # Storage Configuration
    persist_directory: str = 'db'

    # Evaluation Configuration
    eval_sample_rate: float = 0.05
    eval_model: str = 'gpt-4o-mini'

    @classmethod
    def from_env(cls) -> 'RAGConfig':
        """Create config from environment variables with validation."""
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        return cls(
            openai_api_key=openai_key,
            model_name=os.getenv('MODEL_NAME', 'gpt-4.1-nano-2025-04-14'),
            embedding_model=os.getenv('EMBEDDING_MODEL', 'text-embedding-3-large'),
            chunk_size=int(os.getenv('CHUNK_SIZE', '1000')),
            chunk_overlap=int(os.getenv('CHUNK_OVERLAP', '200')),
            retrieval_k=int(os.getenv('RETRIEVAL_K', '6')),
            chain_type=os.getenv('CHAIN_TYPE', 'map_reduce'),
            temperature=float(os.getenv('TEMPERATURE', '0.0')),
            max_tokens=int(os.getenv('MAX_TOKENS', '512')),
            persist_directory=os.getenv('PERSIST_DIRECTORY', 'db'),
            eval_sample_rate=float(os.getenv('EVAL_SAMPLE_RATE', '0.05')),
            eval_model=os.getenv('RAG_EVAL_MODEL', 'gpt-4o-mini'),
        )

# Global config instance
_config: RAGConfig | None = None

def get_config() -> RAGConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = RAGConfig.from_env()
    return _config

# Legacy compatibility functions
def get_openai_api_key() -> str:
    """Legacy function for backward compatibility."""
    return get_config().openai_api_key

# Legacy constants for backward compatibility
MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4.1-nano-2025-04-14')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-large')
CHAIN_TYPE = os.getenv('CHAIN_TYPE', 'map_reduce')
PERSIST_DIRECTORY = os.getenv('PERSIST_DIRECTORY', 'db')

# File Paths
SAMPLE_PDF = Path(__file__).resolve().parent.parent / 'raw_data' / 'rag_intensive_nlp_tasks.pdf'
