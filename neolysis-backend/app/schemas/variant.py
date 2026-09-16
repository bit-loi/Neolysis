from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.property import TargetConditions
from app.schemas.scientific import UncertaintyEstimate


class VariantCandidate(BaseModel):
    variant_id: str = Field(..., min_length=1)
    name: Optional[str] = None
    sequence: Optional[str] = None
    mutations: List[str] = Field(default_factory=list)


class VariantRankRequest(BaseModel):
    wild_type_sequence: str = Field(..., min_length=1)
    variants: List[VariantCandidate] = Field(..., min_length=1)
    target_conditions: TargetConditions = Field(default_factory=TargetConditions)


class MutationRiskRequest(BaseModel):
    wild_type_sequence: str = Field(..., min_length=1)
    variant_sequence: Optional[str] = None
    mutations: List[str] = Field(default_factory=list)
    active_site_positions: List[int] = Field(default_factory=list)
    conserved_regions: List[str] = Field(default_factory=list)


class MutationRiskResult(BaseModel):
    risk_level: str
    risk_score: float = Field(..., ge=0, le=1)
    potential_stability_risk: List[str] = Field(default_factory=list)
    potential_function_risk: List[str] = Field(default_factory=list)
    conserved_region_warning: Optional[str] = None
    active_site_warning: Optional[str] = None
    confidence: float = Field(..., ge=0, le=1)
    uncertainty: Optional[UncertaintyEstimate] = None
    limitations: List[str] = Field(default_factory=list)


class VariantSignals(BaseModel):
    """
    Explainable components behind a variant's rank, instead of one opaque
    "AI score". Any signal this layer cannot compute is left as None with an
    explicit status — never fabricated.

    IMPORTANT: proteinmpnn_compatibility is a backbone-conditioned sequence
    design/compatibility signal (see app/schemas/structure.py), NOT a
    predicted \u0394\u0394G value. This field must never be interpreted as stability.
    """

    thermostability_delta: Optional[float] = Field(
        None, description="Variant thermostability score minus wild-type thermostability score."
    )
    solubility_delta: Optional[float] = None
    ph_fit_delta: Optional[float] = None
    proteinmpnn_compatibility: Optional[float] = Field(
        None,
        description="Backbone-conditioned sequence design/compatibility signal from ProteinMPNN. Not a \u0394\u0394G value.",
    )
    proteinmpnn_status: str = "not_available"  # "not_available" | "completed"
    active_site_distance_angstrom: Optional[float] = Field(
        None, description="3D distance to the nearest active-site residue, when structure context is available."
    )
    structure_prediction_confidence: Optional[float] = None


class RankedVariant(BaseModel):
    rank: int
    variant_id: str
    name: Optional[str] = None
    mutation_summary: str
    predicted_fit_score: float = Field(..., ge=0, le=1)
    risk_score: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    wet_lab_priority: str
    explanation: str
    risk_flags: List[str] = Field(default_factory=list)
    # ── Explainable ranking signals (added, additive/optional) ──────────────
    signals: Optional[VariantSignals] = None
    reasoning: List[str] = Field(default_factory=list)
    calibration_status: str = "uncalibrated"


class VariantRankResponse(BaseModel):
    ranked_variants: List[RankedVariant]
    limitations: List[str] = Field(default_factory=list)
