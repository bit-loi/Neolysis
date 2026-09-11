from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class UncertaintyEstimate(BaseModel):
    """Transparent uncertainty metadata; never presented as statistical calibration."""

    confidence: float = Field(..., ge=0, le=1)
    uncertainty: float = Field(..., ge=0, le=1)
    level: Literal["low", "medium", "high"]
    basis: List[str] = Field(default_factory=list)
    calibration_status: Literal["uncalibrated", "externally_calibrated"] = "uncalibrated"


class ComponentProvenance(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    component: str
    method: str
    model_version: str
    status: Literal["completed", "skipped", "fallback"] = "completed"


class AnalysisProvenance(BaseModel):
    analysis_id: str
    created_at: datetime
    input_sha256: str
    deterministic_seed: int
    components: List[ComponentProvenance] = Field(default_factory=list)
    llm_used: bool = False
    llm_model: Optional[str] = None
    llm_policy: str = (
        "The LLM may explain structured tool outputs but may not create or modify scientific scores."
    )
