"""Application configuration loaded from environment variables."""

import os
from datetime import timedelta
from typing import ClassVar

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///linguapath.db")
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql+psycopg2://", 1)
    elif SQLALCHEMY_DATABASE_URI.startswith("postgresql://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgresql://", "postgresql+psycopg2://", 1)
    SQLALCHEMY_ENGINE_OPTIONS: ClassVar[dict[str, bool]] = {"pool_pre_ping": True}
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    WTF_CSRF_TIME_LIMIT = None
    LLM_MODEL = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")
    DAILY_MESSAGE_CAP = int(os.environ.get("DAILY_MESSAGE_CAP", "50"))
    RATE_LIMIT_CHAT = os.environ.get("RATE_LIMIT_CHAT", "30 per minute")
    ADMIN_EMAILS: ClassVar[set[str]] = {
        email.strip().lower() for email in os.environ.get("ADMIN_EMAILS", "").split(",") if email.strip()
    }
    ALPHA = 0.12
    MAX_STEP = 80.0
    EVALUATOR_RETRY_COUNT = 1
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret-key"
    GROQ_API_KEY = "test-key"
    RATELIMIT_ENABLED = False
