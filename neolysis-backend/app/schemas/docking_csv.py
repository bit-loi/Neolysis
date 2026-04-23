from pydantic import BaseModel
from typing import List, Optional


class DockingCSVResult(BaseModel):
    target: str
    pocket: int
    cid: int
    name: str
    smiles: str
    mw: float
    logp: float
    affinity: float
    ligand_eff: float
    affinity_rank: float
    le_rank: float
    composite: float
    confidence: float
    explanation: Optional[str] = None


class DockingCSVResponse(BaseModel):
    target: str
    compounds: List[DockingCSVResult]