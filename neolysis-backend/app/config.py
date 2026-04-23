from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Neolysis API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/neolysis"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # LLM (Google AI Studio / Gemini API)
    GOOGLE_API_KEY: Optional[str] = None
    LLM_MODEL_NAME: str = "gemma-4-26b-a4b-it"

    # ☁️ Cloudflare R2 — Public read URL for PDB files
    # Format: https://pub-xxxx.r2.dev
    # Set this once you have your R2 bucket configured.
    R2_PUBLIC_BASE_URL: Optional[str] = None

    # External APIs
    PUBCHEM_BASE_URL: str = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    ALPHAFOLD_BASE_URL: str = "https://alphafold.ebi.ac.uk/files"
    RCSB_PDB_BASE_URL: str = "https://files.rcsb.org/download"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
