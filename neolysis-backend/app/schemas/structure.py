"""
Neolysis — Structure Prediction Schemas
==========================================
"""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


StructureModel = Literal["alphafold2", "alphafold2_multimer", "openfold3", "boltz2"]
JobStatus = Literal["queued", "running", "completed", "failed"]


class LigandInput(BaseModel):
    """
    Minimal ligand descriptor for Boltz-2 protein+ligand requests. Field names
    are intentionally conservative; verify against the live NVIDIA Boltz-2
    schema before wiring a real ligand payload (see StructureService docstring).
    """

    id: str
    smiles: str


class StructureJobRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model: StructureModel = Field(..., description="alphafold2 | alphafold2_multimer | openfold3 | boltz2")
    sequences: List[str] = Field(..., min_length=1, description="One sequence for monomer models, 2+ for multimer.")
    ligands: List[LigandInput] = Field(default_factory=list, description="Boltz-2 only. Do not run by default.")
    predict_affinity: bool = Field(False, description="Boltz-2 only, requires at least one ligand.")
    relax_prediction: bool = False
    algorithm: Optional[str] = Field(None, description="e.g. mmseqs2 (AlphaFold2) or jackhmmer (Multimer).")


class StructureJobRecord(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    job_id: str
    job_type: str = "structure_prediction"
    provider: str = "nvidia"
    model: StructureModel
    status: JobStatus
    parameter_hash: str
    sequence_sha256: List[str]
    cache_key: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    requested_model: Optional[str] = None
    actual_model: Optional[str] = None
    fallback_reason: Optional[str] = None


class StructureResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    structure_id: str
    format: str = "pdb"
    provider: str = "nvidia"
    model: StructureModel
    artifact_text: Optional[str] = Field(
        None, description="Inline structure text for this MVP. See StructureService docstring re: object storage."
    )
    confidence_summary: Optional[Dict[str, Any]] = None
    raw_provider_response_keys: List[str] = Field(default_factory=list)


class StructureJobStatusResponse(BaseModel):
    job: StructureJobRecord
    result: Optional[StructureResult] = None


# ── MSA Search ────────────────────────────────────────────────────────────────

class MsaSearchRequest(BaseModel):
    sequence: str = Field(..., min_length=1)
    databases: List[str] = Field(default_factory=lambda: ["all"])
    output_alignment_formats: List[str] = Field(default_factory=lambda: ["a3m"])


class MsaSearchResult(BaseModel):
    sequence_sha256: str
    databases: List[str]
    cache_key: str
    cache_hit: bool
    alignment_formats: List[str]
    raw_provider_response_keys: List[str] = Field(default_factory=list)


# ── ProteinMPNN ────────────────────────────────────────────────────────────────

class ProteinMpnnRequest(BaseModel):
    input_pdb: str = Field(..., min_length=1, description="Backbone/structure in PDB text format.")
    ca_only: bool = False
    use_soluble_model: bool = True
    num_seq_per_target: int = Field(8, ge=1, le=64)
    sampling_temp: List[float] = Field(default_factory=lambda: [0.1])


class ProteinMpnnDesign(BaseModel):
    sequence: str
    # Intentionally NOT named ddg or predicted_ddg — ProteinMPNN is not a ΔΔG
    # model. This is a backbone-conditioned sequence design/compatibility score.
    backbone_sequence_compatibility: Optional[float] = None


class ProteinMpnnResult(BaseModel):
    designs: List[ProteinMpnnDesign]
    cache_key: str
    cache_hit: bool
    method: str = "proteinmpnn_backbone_conditioned_design"
    limitations: List[str] = Field(
        default_factory=lambda: [
            "ProteinMPNN predicts amino-acid sequences compatible with the given backbone; "
            "it is not a \u0394\u0394G (ddg) predictor.",
            "backbone_sequence_compatibility is a design/compatibility signal, not a stability measurement.",
        ]
    )
