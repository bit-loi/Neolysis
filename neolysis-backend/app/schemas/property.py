from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.sequence import SequenceInput
from app.schemas.scientific import UncertaintyEstimate


class TargetConditions(BaseModel):
    temperature_c: Optional[float] = Field(
        None,
        ge=-20,
        le=130,
        description="Target process temperature in Celsius.",
    )
    ph: Optional[float] = Field(None, ge=0, le=14, description="Target process pH.")
    salinity_m_m: Optional[float] = Field(
        None,
        ge=0,
        le=5000,
        description="Approximate salt concentration in mM.",
    )
    solvent_exposure: Optional[str] = Field(
        "none",
        description="none, low, moderate, or high.",
    )
    use_case: Optional[str] = Field(
        "custom",
        description="detergent, food biotech, textile, biofuel, academic research, or custom.",
    )
    notes: Optional[str] = None


class PropertyScoreRequest(SequenceInput):
    target_conditions: TargetConditions = Field(default_factory=TargetConditions)


class PropertyIndicator(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    score: Optional[float] = Field(None, ge=0, le=1)
    label: str
    explanation: str
    # ── Model adapter provenance (added, additive/optional for backward compatibility) ──
    method: str = "heuristic_v1"
    calibration_status: str = "uncalibrated"
    status: str = "heuristic"  # "trained" | "heuristic" | "unavailable"


class PropertyScoreResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    thermostability: PropertyIndicator
    ph_fit: PropertyIndicator
    solubility: PropertyIndicator
    condition_fit: PropertyIndicator
    industrial_fit_score: float = Field(..., ge=0, le=1)
    risk_flags: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0, le=1)
    uncertainty: Optional[UncertaintyEstimate] = None
    method: str
    model_version: str
    limitations: List[str] = Field(default_factory=list)
