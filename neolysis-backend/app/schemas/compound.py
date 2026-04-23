from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class CompoundBase(BaseModel):
    pubchem_cid: int
    name: Optional[str] = None
    canonical_smiles: Optional[str] = None
    molecular_weight: Optional[float] = None
    logp: Optional[float] = None
    hbd: Optional[int] = None
    hba: Optional[int] = None
    qed_score: Optional[float] = None
    lipinski_pass: Optional[bool] = None

class CompoundCreate(CompoundBase):
    pass

class CompoundOut(CompoundBase):
    id: int
    retrieved_at: datetime

    model_config = ConfigDict(from_attributes=True)
