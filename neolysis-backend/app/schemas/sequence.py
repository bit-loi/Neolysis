from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SequenceInput(BaseModel):
    sequence: str = Field(
        ...,
        min_length=1,
        description="Protein FASTA text or raw amino acid sequence.",
    )
    name: Optional[str] = Field(None, description="Optional user-facing sequence name.")


class SequenceValidationResult(BaseModel):
    valid: bool
    name: Optional[str] = None
    cleaned_sequence: str
    sequence_length: int
    invalid_residues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    detected_format: str = "raw"


class ProteinFeatureResult(BaseModel):
    sequence_length: int
    amino_acid_composition: Dict[str, int]
    amino_acid_percent: Dict[str, float]
    molecular_weight: float
    gravy: Optional[float] = None
    aromaticity: Optional[float] = None
    instability_index: Optional[float] = None
    isoelectric_point: Optional[float] = None
    method: str
    warnings: List[str] = Field(default_factory=list)


class SequenceFeatureResponse(BaseModel):
    validation: SequenceValidationResult
    features: Optional[ProteinFeatureResult] = None
