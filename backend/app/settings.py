from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "local-384")
    llm_provider: str = os.getenv("LLM_PROVIDER", "stub")  # stub | openrouter
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    vector_store: str = os.getenv("VECTOR_STORE", "qdrant")
    collection_name: str = os.getenv("COLLECTION_NAME", "policy_helper")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "700"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "80"))
    data_dir: str = os.getenv("DATA_DIR", "/app/data")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()