from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SequenceInput(BaseModel):
    sequence: str = Field(
        ...,
        min_length=1,
        description="Protein FASTA text or raw amino acid sequence.",
    )
    name: Optional[str] = Field(None, description="Optional user-facing sequence name.")
    target_ph: float = Field(
        7.0,
        ge=0.0,
        le=14.0,
        description="pH used to estimate net charge in /sequences/features. Ignored by /sequences/validate.",
    )


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
    # ── Provenance (added: canonical hash of the sequence these features were computed from) ──
    sequence_sha256: Optional[str] = None
    # ── pH-dependent charge estimate (added) ──────────────────────────────────────────────────
    target_ph: Optional[float] = Field(
        None,
        ge=0.0,
        le=14.0,
        description="The pH used to compute charge_at_target_ph (default 7.0 when not specified by the caller).",
    )
    charge_at_target_ph: Optional[float] = Field(
        None,
        description="Estimated net charge at target_ph, from Biopython ProteinAnalysis.charge_at_pH().",
    )
    # ── Ionizable residue composition (added) ─────────────────────────────────────────────────
    ionizable_residue_counts: Optional[Dict[str, int]] = Field(
        None,
        description="Raw counts of D, E, H, K, R (the residues most relevant to charge/pH behavior).",
    )
    ionizable_residue_fractions: Optional[Dict[str, float]] = Field(
        None,
        description="Fraction of sequence length represented by each of D, E, H, K, R.",
    )
    method: str
    warnings: List[str] = Field(default_factory=list)


class SequenceFeatureMetadata(BaseModel):
    """
    Non-scientific metadata describing how a result was produced. Kept separate from
    ProteinFeatureResult so that `features` stays a pure set of deterministic descriptors,
    and so this shape can be reused by future model-backed results (embeddings, structure,
    property models, etc.) without cluttering their numeric payloads.
    """

    method: str
    interpretation: str = "deterministic_sequence_descriptor"
    calibration_required: bool = False
    disclaimer: str = (
        "These descriptors are computational sequence properties and are not experimental measurements."
    )


class SequenceFeatureResponse(BaseModel):
    validation: SequenceValidationResult
    features: Optional[ProteinFeatureResult] = None
    metadata: Optional[SequenceFeatureMetadata] = None
