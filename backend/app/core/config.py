"""Centralized application configuration.

Values are read from environment variables (see .env.example). Nothing here
is a placeholder -- every setting is actually consumed by the application.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ZeroDay Security AI API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]

    # Logging
    log_level: str = "INFO"

    # Database. Defaults to a local SQLite file so the API runs with zero
    # external services in development; set DATABASE_URL to a Postgres DSN
    # (e.g. postgresql+asyncpg://user:pass@host/db) in staging/production.
    database_url: str = "sqlite+aiosqlite:///./zeroday.db"

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v or "sqlite+aiosqlite:///./zeroday.db"

    # Auth / JWT. jwt_secret_key MUST be overridden via env var in any
    # deployed environment -- the default is for local dev only.
    jwt_secret_key: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7

    # ── LLM Provider selection ───────────────────────────────────────────────
    # Set LLM_PROVIDER to one of: nvidia | groq | gemini | ollama | anthropic
    # Then set the matching API key / config below.
    llm_provider: str = "groq"          # Groq is free with no credit card
    assistant_max_tool_rounds: int = 4

    # NVIDIA NIM (Nemotron Ultra / Super / Llama)
    # Free API key: https://build.nvidia.com
    nvidia_api_key: str | None = None
    nvidia_model: str = "nvidia/llama-3.1-nemotron-ultra-253b-v1"

    # Groq (free tier, fast inference)
    # Free API key: https://console.groq.com
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    # Google Gemini (user has Pro)
    # Key at: https://aistudio.google.com/apikey
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"

    # Ollama (local, no key needed)
    # Install: https://ollama.ai  then: ollama pull llama3.2
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Anthropic Claude (kept as option)
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-6"


@lru_cache
def get_settings() -> Settings:
    return Settings()
