import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # DATABASE CONFIG
    DB_HOST = os.getenv("DB_HOST")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_NAME = os.getenv("DB_NAME")
    DB_PORT = os.getenv("DB_PORT")


    # LLM CONFIG
    VLLM_URL = os.getenv("VLLM_URL")
    VLLM_MODEL = os.getenv("VLLM_MODEL")
    VLLM_API_KEY = os.getenv("VLLM_API_KEY")

    # RAG CONFIG
    EMBEDDING_API = os.getenv("EMBEDDING_API")
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "qdrant_db")
    COLLECTION_NAME = os.getenv("SCHEMA_COLLECTION", "schema_collection")
settings = Settings()
