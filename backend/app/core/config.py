"""Application settings, loaded from environment variables (and backend/.env).

Every setting is environment-driven so the same image can run in development,
test and production without code changes.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application -------------------------------------------------------
    APP_NAME: str = "Attestive API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # --- Security ----------------------------------------------------------
    # No usable default in production: validated below.
    SECRET_KEY: str = "insecure-development-key-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    REFRESH_COOKIE_NAME: str = "sf_refresh"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    PASSWORD_MIN_LENGTH: int = 8

    # Account lockout: N failed passwords lock the account for a cooling window.
    MAX_FAILED_LOGINS: int = 5
    LOCKOUT_MINUTES: int = 15

    # --- Email delivery ----------------------------------------------------
    # console/disabled are development paths; resend/sendgrid/smtp deliver mail.
    APP_BASE_URL: str = "http://localhost:5173"
    EMAIL_DELIVERY: Literal["console", "disabled", "resend", "sendgrid", "smtp"] = "console"
    # RFC 5322 form, e.g. "Attestive <no-reply@mail.example.com>"
    EMAIL_FROM: str = "Attestive <no-reply@localhost>"
    EMAIL_API_KEY: str | None = None
    EMAIL_TIMEOUT_SECONDS: int = 10
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_STARTTLS: bool = True
    VERIFY_TOKEN_TTL_HOURS: int = 48
    RESET_TOKEN_TTL_MINUTES: int = 60

    # --- Rate limiting -----------------------------------------------------
    # Per-process sliding window. A multi-instance deployment needs a shared
    # store; the runbook documents that limitation.
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_PER_MINUTE: int = 20
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 120

    # --- Database ----------------------------------------------------------
    # Production: postgresql+asyncpg://attestive:attestive@db:5432/attestive
    # Local development fallback: SQLite (async) so the stack runs without Docker.
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/attestive.db"
    DB_ECHO: bool = False

    # --- Frontend / CORS ---------------------------------------------------
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    ADDITIONAL_ORIGINS: list[str] = Field(default_factory=list)

    # --- AI (used from Phase 3 onwards) -----------------------------------
    # openai = any OpenAI-compatible hosted API (OpenAI, Groq, Together, vLLM,
    # …); disabled = deterministic only.
    AI_PROVIDER: Literal["openai", "disabled"] = "openai"
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    # The roadmap sequence is deterministic and validated; the model only writes
    # the plan note. Disabled automatically when the provider is unreachable.
    AI_ROADMAP_ENABLED: bool = True
    ROADMAP_AI_TIMEOUT_SECONDS: int = 12

    # --- Hosted model provider (AI_PROVIDER=openai) ------------------------
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: str | None = None
    OPENAI_TIMEOUT_SECONDS: int = 60

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalise_database_url(cls, value: str) -> str:
        """Accept the URL forms Docker/Heroku hand out and force async drivers."""
        if value.startswith("postgres://"):
            value = value.replace("postgres://", "postgresql+asyncpg://", 1)
        elif value.startswith("postgresql://"):
            value = value.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif value.startswith("sqlite://") and "+aiosqlite" not in value:
            value = value.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return value

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def email_configured(self) -> bool:
        return self.EMAIL_DELIVERY in {"resend", "sendgrid", "smtp"}

    @property
    def cors_origins(self) -> list[str]:
        return [self.FRONTEND_ORIGIN, *self.ADDITIONAL_ORIGINS]

    def validate_for_runtime(self) -> None:
        if self.ENVIRONMENT == "production":
            problems: list[str] = []
            if self.SECRET_KEY.startswith("insecure-") or len(self.SECRET_KEY) < 32:
                problems.append("SECRET_KEY must be a random value of at least 32 characters")
            if not self.COOKIE_SECURE:
                problems.append("COOKIE_SECURE must be true in production")
            if self.is_sqlite:
                problems.append("DATABASE_URL must point at PostgreSQL in production")
            if not self.APP_BASE_URL.startswith("https://"):
                problems.append("APP_BASE_URL must use https in production")
            if not self.RATE_LIMIT_ENABLED:
                problems.append("RATE_LIMIT_ENABLED must be true in production")
            if self.EMAIL_DELIVERY in {"resend", "sendgrid"} and not self.EMAIL_API_KEY:
                problems.append(
                    f"EMAIL_API_KEY is required when EMAIL_DELIVERY={self.EMAIL_DELIVERY}"
                )
            if self.EMAIL_DELIVERY == "smtp" and not self.SMTP_HOST:
                problems.append("SMTP_HOST is required when EMAIL_DELIVERY=smtp")
            if problems:
                raise RuntimeError("Invalid production configuration: " + "; ".join(problems))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
