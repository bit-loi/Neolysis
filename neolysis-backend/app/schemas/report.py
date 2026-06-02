from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.enzyme import EnzymeFunctionPrediction
from app.schemas.property import PropertyScoreResult, TargetConditions
from app.schemas.sequence import ProteinFeatureResult, SequenceValidationResult
from app.schemas.variant import VariantRankResponse


WET_LAB_DISCLAIMER = (
    "These results are computational estimates intended for candidate "
    "prioritization. Experimental wet-lab validation is required before "
    "industrial use."
)


class ReportGenerationRequest(BaseModel):
    sequence_validation: SequenceValidationResult
    protein_features: Optional[ProteinFeatureResult] = None
    enzyme_prediction: Optional[EnzymeFunctionPrediction] = None
    property_scoring: Optional[PropertyScoreResult] = None
    variant_ranking: Optional[VariantRankResponse] = None
    target_conditions: TargetConditions = Field(default_factory=TargetConditions)
    user_question: Optional[str] = None


class ValidationPlanItem(BaseModel):
    step: str
    rationale: str


class ReportResponse(BaseModel):
    executive_summary: str
    markdown_report: str
    json_report: Dict[str, Any]
    recommended_wet_lab_validation_plan: List[ValidationPlanItem]
    limitations: List[str] = Field(default_factory=list)
    disclaimer: str = WET_LAB_DISCLAIMER
