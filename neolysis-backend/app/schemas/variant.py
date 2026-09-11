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


class VariantRankResponse(BaseModel):
    ranked_variants: List[RankedVariant]
    limitations: List[str] = Field(default_factory=list)
