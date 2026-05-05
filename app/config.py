"""
NEXUS — Centralised Configuration
===================================
Uses Pydantic BaseSettings to load every environment variable from .env
and expose them as a typed, validated singleton across the application.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── App ────────────────────────────────────────────────────────────────
    APP_NAME: str = "NEXUS"
    APP_ENV: str = "development"       # development | staging | production
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ── Auth ───────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-this-to-a-random-64-char-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # ── Admin seed user ────────────────────────────────────────────────────
    ADMIN_EMAIL: str = "admin@nexus.local"
    ADMIN_PASSWORD: str = "changeme123"

    # ── Server ─────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["*"]

    # ── Database ────────────────────────────────────────────────────────────
    # SQLite for local dev; override with PostgreSQL URL in production .env
    DATABASE_URL: str = "sqlite:///./nexus.db"

    # ── Redis ──────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── ChromaDB ───────────────────────────────────────────────────────────
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8100
    CHROMA_COLLECTION: str = "nexus_vectors"

    # ── Storage ────────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # ── LLM Generation & Provider Selection ────────────────────────────────
    LLM_PROVIDER: str = "groq"
    LLM_AUTO_FALLBACK: bool = True

    # Groq (Primary — Free)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Google Gemini (Secondary — Free)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Ollama (Tertiary — Local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3:mini"

    # OpenAI (Optional)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── Whisper (audio transcription) ──────────────────────────────────────
    WHISPER_MODEL_SIZE: str = "base"   # tiny | base | small | medium | large
    WHISPER_MODEL: str = "base"        # canonical alias used by AudioExtractor
    AUDIO_MAX_WORDS_PER_CHUNK: int = 120
    AUDIO_OVERLAP_WORDS: int = 15

    # ── Celery / Task Queue ────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "sqla+sqlite:///./celery_broker.db"
    CELERY_RESULT_BACKEND: str = "db+sqlite:///./celery_backend.db"

    # ── Embeddings & Vector Store ──────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHROMA_PERSIST_PATH: str = "./chroma_data"
    DEFAULT_TOP_K: int = 10
    CLIP_MODEL: str = "openai/clip-vit-base-patch32"
    TESSERACT_AVAILABLE: bool = True

    # ── Graph Database & Linking ───────────────────────────────────────────
    GRAPH_PERSIST_PATH: str = "./graph_data/nexus_graph.json"
    SEMANTIC_LINK_THRESHOLD: float = 0.75
    ENTITY_LINK_MIN_SHARED: int = 2
    TEMPORAL_LINK_WINDOW_SECONDS: float = 10.0


# Singleton settings instance — import this everywhere
settings = Settings()
