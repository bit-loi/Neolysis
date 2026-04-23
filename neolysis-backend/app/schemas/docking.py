from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
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
