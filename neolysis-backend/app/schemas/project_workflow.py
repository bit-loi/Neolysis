from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.sequence import ProteinFeatureResult, SequenceValidationResult


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    description: Optional[str] = None
    enzyme_target: Optional[str] = None
    enzyme_name: Optional[str] = None
    objective: Optional[str] = None
    organism_source: Optional[str] = None
    target_industry: Optional[str] = None
    status: str = "active"
    user_id: Optional[str] = None


class ProjectRecord(ProjectCreateRequest):
    id: str
    created_at: datetime
    updated_at: datetime


class EnzymeSequenceRequest(BaseModel):
    sequence: str = Field(..., min_length=1)
    name: Optional[str] = None


class EnzymeSequenceRecord(BaseModel):
    id: str
    project_id: str
    sequence: str
    sequence_length: int
    length: int
    molecular_weight: Optional[float] = None
    pI: Optional[float] = None
    instability_index: Optional[float] = None
    GRAVY: Optional[float] = None
    aromaticity: Optional[float] = None
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    validation: SequenceValidationResult
    feature_json: Optional[ProteinFeatureResult] = None
    created_at: datetime


class EnzymeStructureRequest(BaseModel):
    source_type: str = Field(
        "uploaded_pdb",
        description="uploaded_pdb, pdb_id, alphafold_db, or predicted_placeholder.",
    )
    source: Optional[str] = Field(
        None,
        description="Product-level source label: uploaded, alphafold_db, predicted, or pdb_id.",
    )
    pdb_id: Optional[str] = None
    alphafold_id: Optional[str] = None
    chain_id: Optional[str] = None
    raw_pdb_text: Optional[str] = None
    uploaded_pdb_path: Optional[str] = None
    storage_path: Optional[str] = None
    structure_notes: Optional[str] = None

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        allowed = {"uploaded_pdb", "pdb_id", "alphafold_db", "predicted_placeholder"}
        if value not in allowed:
            raise ValueError(f"source_type must be one of {', '.join(sorted(allowed))}")
        return value


class EnzymeStructureRecord(EnzymeStructureRequest):
    id: str
    project_id: str
    confidence_notes: List[str] = Field(default_factory=list)
    created_at: datetime


class SubstrateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    smiles: str = Field(..., min_length=1, max_length=1000)
    sdf_path: Optional[str] = None
    role: str = "substrate"
    notes: Optional[str] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        allowed = {"substrate", "product", "inhibitor", "analog"}
        if value not in allowed:
            raise ValueError(f"role must be one of {', '.join(sorted(allowed))}")
        return value


class SubstrateRecord(SubstrateRequest):
    id: str
    project_id: str
    validation_notes: List[str] = Field(default_factory=list)
    created_at: datetime


class ActiveSiteRequest(BaseModel):
    structure_id: str
    name: str = Field("Active site", min_length=1, max_length=160)
    residues: List[str] = Field(..., min_length=1)
    selection_method: str = "manual"
    notes: Optional[str] = None

    @field_validator("selection_method")
    @classmethod
    def validate_selection_method(cls, value: str) -> str:
        allowed = {"manual", "pocket_prediction_placeholder"}
        if value not in allowed:
            raise ValueError(f"selection_method must be one of {', '.join(sorted(allowed))}")
        return value


class ActiveSiteRecord(BaseModel):
    id: str
    project_id: str
    structure_id: str
    name: str
    residue_list: List[str]
    residue_positions: List[int]
    nearby_residues: List[str] = Field(default_factory=list)
    mutation_candidate_residues: List[str] = Field(default_factory=list)
    protected_residues: List[str] = Field(default_factory=list)
    selection_method: str
    notes: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    created_at: datetime


class VariantGenerateRequest(BaseModel):
    max_variants: int = Field(12, ge=1, le=60)
    allow_catalytic_mutations: bool = False
    target_residues: List[str] = Field(default_factory=list)


class EnzymeVariantRecord(BaseModel):
    id: str
    project_id: str
    mutation_label: str
    wild_type_residue: str
    position: int
    mutant_residue: str
    reason: str
    active_site_distance_proxy: Optional[float] = None
    sequence_property_score: Optional[float] = None
    active_site_relevance_score: Optional[float] = None
    stability_proxy_score: Optional[float] = None
    binding_proxy_score: Optional[float] = None
    docking_score_normalized: Optional[float] = None
    mutation_risk_score: Optional[float] = None
    final_score: Optional[float] = None
    explanation: str
    warnings: List[str] = Field(default_factory=list)
    created_at: datetime


class AnalysisReportRecord(BaseModel):
    id: str
    project_id: str
    report_type: str
    summary: str
    top_variants: List[Dict[str, Any]] = Field(default_factory=list)
    wet_lab_plan: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    markdown_report: str
    report_json: Dict[str, Any]
    created_at: datetime


class DockingJobRequest(BaseModel):
    structure_id: Optional[str] = None
    substrate_id: Optional[str] = None
    status: str = "queued"
    grid_center: Optional[Dict[str, float]] = None
    grid_size: Optional[Dict[str, float]] = None
    docking_score: Optional[float] = None
    output_pose_path: Optional[str] = None
    interacting_residues: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class DockingJobRecord(DockingJobRequest):
    id: str
    project_id: str
    created_at: datetime


class ProjectDetailResponse(BaseModel):
    project: ProjectRecord
    sequence: Optional[EnzymeSequenceRecord] = None
    structures: List[EnzymeStructureRecord] = Field(default_factory=list)
    substrates: List[SubstrateRecord] = Field(default_factory=list)
    active_sites: List[ActiveSiteRecord] = Field(default_factory=list)
    variants: List[EnzymeVariantRecord] = Field(default_factory=list)
    docking_jobs: List[DockingJobRecord] = Field(default_factory=list)
    reports: List[AnalysisReportRecord] = Field(default_factory=list)
