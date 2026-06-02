from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime


class DockingBase(BaseModel):
    target_id: int
    compound_id: int
    vina_score_kcal_mol: Optional[float] = None
    binding_pose_json: Optional[Dict[str, Any]] = None
    source: str = "precomputed"


class DockingOut(DockingBase):
    id: int
    computed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DockingWithCompound(BaseModel):
    """
    Aggregated docking result with inline compound metadata.
    Used by GET /docking/{target_id} and GET /targets/{id}/compounds.
    """
    compound_id: int
    pubchem_cid: int
    name: Optional[str] = None
    smiles: Optional[str] = None
    molecular_weight: Optional[float] = None
    logp: Optional[float] = None
    hbd: Optional[int] = None
    hba: Optional[int] = None
    qed_score: Optional[float] = None
    lipinski_pass: Optional[bool] = None
    vina_score_kcal_mol: Optional[float] = None
    source: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


DockingEngine = Literal["quickvina2", "smina", "vina"]
DockingStatus = Literal["pending", "preparing", "running", "completed", "failed"]
DockingComputeBackend = Literal["local", "kaggle"]


class DockingGrid(BaseModel):
    x: float
    y: float
    z: float


class DockingJobCreate(BaseModel):
    structure_id: str
    substrate_id: str
    grid_center: DockingGrid
    grid_size: DockingGrid
    engine: DockingEngine = "quickvina2"
    compute_backend: DockingComputeBackend = "local"
    exhaustiveness: int = Field(4, ge=1)

    @field_validator("grid_size")
    @classmethod
    def validate_grid_size(cls, value: DockingGrid) -> DockingGrid:
        if value.x <= 0 or value.y <= 0 or value.z <= 0:
            raise ValueError("grid_size values must be positive")
        return value


class LigandPreparationResult(BaseModel):
    ligand_sdf_path: Optional[str] = None
    ligand_pdbqt_path: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    success: bool
    error_message: Optional[str] = None


class ReceptorPreparationResult(BaseModel):
    receptor_pdb_path: Optional[str] = None
    receptor_pdbqt_path: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    success: bool
    error_message: Optional[str] = None


class DockingResultRecord(BaseModel):
    id: str
    docking_job_id: str
    binding_affinity: float
    pose_rank: int
    rmsd_lb: Optional[float] = None
    rmsd_ub: Optional[float] = None
    output_pose_path: str
    output_log_path: str
    interacting_residues_json: Dict[str, Any]
    distance_cutoff_angstrom: float = 4.0
    raw_engine_output: Optional[str] = None
    execution_backend: DockingComputeBackend = "local"
    remote_kernel_ref: Optional[str] = None
    created_at: datetime


class DockingJobRecord(BaseModel):
    id: str
    project_id: str
    structure_id: str
    substrate_id: str
    receptor_source_path: Optional[str] = None
    receptor_storage_path: Optional[str] = None
    ligand_source_smiles: Optional[str] = None
    ligand_storage_path: Optional[str] = None
    grid_center_x: float
    grid_center_y: float
    grid_center_z: float
    grid_size_x: float
    grid_size_y: float
    grid_size_z: float
    engine: DockingEngine = "quickvina2"
    compute_backend: DockingComputeBackend = "local"
    exhaustiveness: int
    status: DockingStatus = "pending"
    error_message: Optional[str] = None
    remote_kernel_ref: Optional[str] = None
    remote_output_path: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DockingJobWithResult(BaseModel):
    job: DockingJobRecord
    result: Optional[DockingResultRecord] = None


class DockingPoseResponse(BaseModel):
    job_id: str
    output_pose_path: Optional[str] = None
    pose_text: Optional[str] = None
