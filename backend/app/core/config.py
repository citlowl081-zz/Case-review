"""Application configuration via pydantic-settings."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # --- Application ---
    APP_NAME: str = "Clinical Trial Document Review RAG Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # --- Alibaba Cloud DashScope (百炼) ---
    DASHSCOPE_API_KEY: str = ""
    LLM_MODEL_NAME: str = "qwen3-max"
    EMBEDDING_MODEL: str = "text-embedding-v2"
    DASHSCOPE_BASE_URL: str = "https://ws-ujry5px7m5k2m903.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
    DASHSCOPE_API_URL: str = "https://ws-ujry5px7m5k2m903.cn-beijing.maas.aliyuncs.com/api/v1"
    LLM_TEMPERATURE: float = 0.3          # 低温保证准确性
    LLM_MAX_TOKENS: int = 4096

    # --- Database (PostgreSQL) ---
    # --- Database (PostgreSQL for production, SQLite for development) ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./langchain_rag.db"

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300             # 检索缓存 5 分钟

    # --- JWT ---
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # --- ChromaDB ---
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "chroma_data")
    CHROMA_COLLECTION_NAME: str = "clinical_trials"

    # --- File Upload ---
    UPLOAD_DIR: str = str(BASE_DIR / "storage" / "docs")
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = [".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".xlsx"]

    # --- Document Processing ---
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # --- Retrieval ---
    RETRIEVAL_TOP_K: int = 5
    HYBRID_TOP_K: int = 10

    # --- Rate Limiting ---
    RATE_LIMIT_PER_USER: int = 20          # 每用户每分钟
    RATE_LIMIT_GLOBAL: int = 200           # 全局限流

    # --- Celery ---
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # --- Admin Default ---
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""

    # --- App Access ---
    APP_PASSWORD: str = "qc2026"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra env vars (e.g., APP_PASSWORD)


settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
