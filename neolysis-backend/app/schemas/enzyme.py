from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.sequence import SequenceInput


class EnzymeFunctionRequest(SequenceInput):
    enzyme_class_hint: Optional[str] = Field(
        None,
        description="Optional enzyme family or EC class hint supplied by the user.",
    )


class EmbeddingResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    vector: List[float]
    dimensions: int
    mode: str
    model_version: str
    limitations: List[str] = Field(default_factory=list)


class EnzymeFunctionPrediction(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    predicted_family: str
    predicted_ec_class: Optional[str] = None
    confidence: float = Field(..., ge=0, le=1)
    explanation: str
    evidence: List[str] = Field(default_factory=list)
    method: str
    model_version: str
    limitations: List[str] = Field(default_factory=list)


class EnzymeFunctionResponse(BaseModel):
    embedding: Optional[EmbeddingResult] = None
    prediction: EnzymeFunctionPrediction
