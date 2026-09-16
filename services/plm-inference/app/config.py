"""
Neolysis — PLM Inference Service Configuration
================================================
"""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PLM_MODEL: str = "facebook/esm2_t30_150M_UR50D"
    PLM_DEVICE: str = "auto"  # "auto" | "cpu" | "cuda"
    PLM_MAX_RESIDUES: int = 1022
    PLM_POOLING: str = "mean"
    HF_TOKEN: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
