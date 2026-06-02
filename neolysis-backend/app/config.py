"""
Neolysis — Application Configuration
======================================
All settings are loaded from environment variables via pydantic-settings.
Never hardcode secrets — always use .env or environment injection.

Supported .env variables:
    DATABASE_URL              — SQLAlchemy async connection string (asyncpg)
    REDIS_URL                 — Redis connection string for caching
    GOOGLE_API_KEY            — Google GenAI API key (Gemma 4)
    QDRANT_HOST               — Qdrant vector DB hostname (default: localhost)
    QDRANT_PORT               — Qdrant port (default: 6333)
    SECRET_KEY                — JWT signing secret (CHANGE IN PRODUCTION)
    R2_PUBLIC_BASE_URL        — Cloudflare R2 public URL for PDB files

Supabase PostgreSQL (native asyncpg — NOT Supabase SDK):
    SUPABASE_DB_HOST          — e.g. db.xxxx.supabase.co
    SUPABASE_DB_USER          — e.g. postgres
    SUPABASE_DB_PASSWORD      — your Supabase DB password
    SUPABASE_DB_NAME          — postgres (default)
    SUPABASE_DB_PORT          — 5432 (default)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────────────────────
    PROJECT_NAME: str = "Neolysis Enzyme Engineering API"
    VERSION: str = "0.2.0-staging"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # ── Security ───────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # ── PostgreSQL / Supabase (native asyncpg — NOT Supabase SDK) ──────────
    # Can be set directly as DATABASE_URL or assembled from SUPABASE_DB_* parts
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/neolysis"

    # Supabase-flavoured individual env vars (alternative to DATABASE_URL)
    SUPABASE_DB_HOST: Optional[str] = None
    SUPABASE_DB_USER: Optional[str] = None
    SUPABASE_DB_PASSWORD: Optional[str] = None
    SUPABASE_DB_NAME: str = "postgres"
    SUPABASE_DB_PORT: int = 5432

    # ── Redis ──────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── LLM (Google GenAI / Gemma 4) ──────────────────────────────────────
    GOOGLE_API_KEY: Optional[str] = None
    LLM_MODEL_NAME: str = "gemma-4-27b-it"

    # ── Qdrant Vector Store ────────────────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # ── RAG / Embedding ────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    PUBMED_MAX_RESULTS: int = 100  # per search term in crawler

    # -- Enzyme engineering staging modes ----------------------------------
    PROTEIN_EMBEDDING_MODE: str = "baseline"
    ENZYME_FUNCTION_MODEL_MODE: str = "baseline"
    PROPERTY_SCORING_MODE: str = "baseline"

    # ── External APIs ──────────────────────────────────────────────────────
    PUBCHEM_BASE_URL: str = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    ALPHAFOLD_BASE_URL: str = "https://alphafold.ebi.ac.uk/files"
    RCSB_PDB_BASE_URL: str = "https://files.rcsb.org/download"

    # ── Cloudflare R2 ──────────────────────────────────────────────────────
    R2_PUBLIC_BASE_URL: Optional[str] = None

    # ── DB Keepalive ───────────────────────────────────────────────────────
    DB_KEEPALIVE_INTERVAL_SECONDS: int = 300  # 5 minutes

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "production", "prod", "false", "0", "no", "off"}:
                return False
            if normalized in {"debug", "development", "dev", "true", "1", "yes", "on"}:
                return True
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    def get_database_url(self) -> str:
        """
        Return the effective database URL.

        Priority:
          1. DATABASE_URL (if set)
          2. Assembled from SUPABASE_DB_* parts
        """
        if self.SUPABASE_DB_HOST and self.SUPABASE_DB_USER and self.SUPABASE_DB_PASSWORD:
            return (
                f"postgresql+asyncpg://{self.SUPABASE_DB_USER}:{self.SUPABASE_DB_PASSWORD}"
                f"@{self.SUPABASE_DB_HOST}:{self.SUPABASE_DB_PORT}/{self.SUPABASE_DB_NAME}"
            )
        return self.DATABASE_URL


settings = Settings()
