"""
Centralized application configuration.

Everything that varies between local/dev/prod is read from environment
variables here, and nowhere else in the codebase. Never hardcode secrets.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "LinkedIQ"
    ENV: str = "development"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://linkediq:linkediq@localhost:5432/linkediq"
    # Set True for hosted Postgres providers that enforce TLS on external
    # connections (e.g. Supabase's connection pooler). Leave False for
    # local/Docker Postgres, which doesn't need it.
    DB_SSL_REQUIRE: bool = False

    # --- Auth ---
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- Chat / generation LLM ---
    # Uses the OpenAI SDK, but the SDK's base_url is fully configurable, so
    # this can point at OpenAI (default) OR any OpenAI-compatible endpoint,
    # including xAI's Grok API (base_url=https://api.x.ai/v1, model=grok-4.3).
    # OPENAI_API_KEY holds whichever provider's key you're using -- the name
    # is kept for backward compatibility with the OpenAI SDK's expectations.
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""  # empty = OpenAI's default endpoint
    OPENAI_CHAT_MODEL: str = "gpt-4o"  # set to "grok-4.3" in .env when using xAI

    # --- Embeddings ---
    # Runs 100% locally via fastembed (ONNX runtime) -- no API key, no cost,
    # no external dependency at request time. This is independent of
    # whichever provider OPENAI_BASE_URL points at, since xAI does not
    # currently expose a public embeddings API.
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384  # dimension of the local embedding model above

    # --- CORS ---
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # --- File upload limits ---
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25MB
    ALLOWED_UPLOAD_EXTENSIONS: tuple[str, ...] = (".csv", ".zip")


@lru_cache
def get_settings() -> Settings:
    return Settings()
