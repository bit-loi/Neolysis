from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class TargetBase(BaseModel):
    name: str
    disease: str
    organism: str
    uniprot_id: str
    alphafold_id: Optional[str] = None
    pdb_id: Optional[str] = None
    # Direct URL to PDB file stored in R2 / AlphaFold / RCSB
    pdb_url: Optional[str] = None
    source: Optional[str] = None
    binding_site_residues: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    asean_prevalence_note: Optional[str] = None

class TargetCreate(TargetBase):
    pass

class TargetOut(TargetBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
