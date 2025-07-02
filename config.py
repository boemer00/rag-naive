from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PERSIST_DIRECTORY = os.getenv('PERSIST_DIRECTORY', 'db')
MODEL_NAME = 'gpt-4.1-nano-2025-04-14'
CHAIN_TYPE = 'map_reduce'  # stuff, map_reduce, map_rerank, re
