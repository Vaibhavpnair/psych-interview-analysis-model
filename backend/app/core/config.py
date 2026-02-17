"""
Application configuration — loads from .env file.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── Database ─────────────────────────────────────
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/psych_interview"

    # ── Redis ────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Security ─────────────────────────────────────
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # ── AI / ML ──────────────────────────────────────
    WHISPER_MODEL_SIZE: str = "base"
    SPACY_MODEL: str = "en_core_web_sm"

    # ── CORS ─────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"

    # ── Storage ──────────────────────────────────────
    UPLOAD_DIR: str = "../data/raw_uploads"
    PROCESSED_DIR: str = "../data/processed"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
