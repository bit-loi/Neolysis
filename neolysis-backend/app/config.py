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
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────────────────────
    PROJECT_NAME: str = "Neolysis Enzyme Engineering API"
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool | str = False

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

    # -- Enzyme engineering feature modes -----------------------------------
    PROTEIN_EMBEDDING_MODE: str = "baseline"
    PROTEIN_EMBEDDING_MODEL: str = "facebook/esm2_t30_150M_UR50D"
    PROTEIN_EMBEDDING_MAX_RESIDUES: int = 1022
    ENZYME_FUNCTION_MODEL_MODE: str = "baseline"
    PROPERTY_SCORING_MODE: str = "baseline"

    # -- Protein Language Model (PLM) inference microservice ----------------
    # This backend never loads ESM2 in-process. When PROTEIN_EMBEDDING_MODE=esm2,
    # embeddings are requested from the dedicated service at PLM_SERVICE_URL
    # (see services/plm-inference). If unset/unreachable, embeddings fall back
    # to the baseline provider with an explicit fallback_reason.
    PLM_SERVICE_URL: Optional[str] = None
    PLM_POOLING: str = "mean"
    HF_TOKEN: Optional[str] = None

    # -- PLM provider selection (Milestone 2A) ------------------------------
    # Explicit provider switch: "hf_space" | "http" | "baseline" (or unset).
    # When set, this takes priority over the legacy PROTEIN_EMBEDDING_MODE +
    # PLM_SERVICE_URL combination (kept for backward compatibility — existing
    # deployments that only set PROTEIN_EMBEDDING_MODE=esm2 + PLM_SERVICE_URL
    # continue to work unchanged when PLM_PROVIDER is left unset).
    PLM_PROVIDER: Optional[str] = None
    # Hugging Face Space id, e.g. "JasonLOi/neolysis-plm". Only used when
    # PLM_PROVIDER=hf_space.
    HF_SPACE_ID: Optional[str] = None
    # Model/max-residues used specifically by the hf_space provider. Kept
    # separate from PROTEIN_EMBEDDING_MODEL/PROTEIN_EMBEDDING_MAX_RESIDUES
    # (which the legacy http provider still uses) to avoid changing existing
    # behavior for deployments already running the http microservice.
    PLM_MODEL: str = "facebook/esm2_t30_150M_UR50D"
    PLM_MAX_RESIDUES: int = 1022

    # -- NVIDIA NIM (structure prediction / MSA / ProteinMPNN) --------------
    # Not configured yet: NVIDIA_API_KEY is intentionally absent from this
    # environment. Endpoints that need it return a clear "not configured"
    # error rather than silently doing nothing when this is unset.
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_HEALTH_API_BASE_URL: Optional[str] = None
    NVIDIA_DEFAULT_STRUCTURE_MODEL: str = "openfold3"
    NVIDIA_REQUEST_TIMEOUT_SECONDS: int = 900
    NVIDIA_MAX_RETRIES: int = 3

    # -- Molecular docking MVP ---------------------------------------------
    QUICKVINA_BIN: Optional[str] = None
    DOCKING_WORKDIR: str = "storage/docking"
    DOCKING_TIMEOUT_SECONDS: int = 300
    KAGGLE_USERNAME: Optional[str] = None
    KAGGLE_KEY: Optional[str] = None
    KAGGLE_OWNER_USERNAME: Optional[str] = None
    KAGGLE_KERNEL_VISIBILITY: str = "private"
    KAGGLE_POLL_INTERVAL_SECONDS: int = 30
    KAGGLE_TIMEOUT_SECONDS: int = 7200

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
            if normalized in {"release", "production", "prod", "false", "0", "no", "off", "warn", "warning"}:
                return False
            if normalized in {"debug", "development", "dev", "true", "1", "yes", "on"}:
                return True
        return value

    model_config = SettingsConfigDict(
        # Local backend config first; Neon CLI's root file overrides it when present.
        env_file=(".env", ".env.local", "../.env.local"),
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
            return self._async_database_url(
                f"postgresql+asyncpg://{self.SUPABASE_DB_USER}:{self.SUPABASE_DB_PASSWORD}"
                f"@{self.SUPABASE_DB_HOST}:{self.SUPABASE_DB_PORT}/{self.SUPABASE_DB_NAME}"
            )
        return self._async_database_url(self.DATABASE_URL)

    @staticmethod
    def _async_database_url(database_url: str) -> str:
        """Convert provider-style PostgreSQL URLs into SQLAlchemy asyncpg URLs."""
        parsed = urlsplit(database_url)
        scheme = parsed.scheme
        if scheme in {"postgres", "postgresql"}:
            scheme = "postgresql+asyncpg"

        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        # Neon emits libpq parameters. asyncpg uses `ssl` and does not accept
        # libpq's channel_binding parameter.
        ssl_mode = query.pop("sslmode", None)
        query.pop("channel_binding", None)
        if ssl_mode and "ssl" not in query:
            query["ssl"] = ssl_mode

        return urlunsplit(
            (scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment)
        )


settings = Settings()
