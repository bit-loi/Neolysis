"""
Neolysis — Pydantic Schemas for Protein
=========================================
Pydantic v2 schemas for protein drug targets.
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProteinBase(BaseModel):
    name: str = Field(..., max_length=255, description="Protein name, e.g. 'NS5 RNA Polymerase'")
    pdb_id: Optional[str] = Field(None, max_length=20, description="RCSB PDB ID")
    alphafold_id: Optional[str] = Field(None, max_length=50, description="AlphaFold UniProt accession")
    disease_id: Optional[uuid.UUID] = Field(None, description="FK to Disease")
    structure_url: Optional[str] = Field(None, description="Direct URL to PDB file")
    sequence: Optional[str] = Field(None, description="Raw FASTA amino acid sequence")


class ProteinCreate(ProteinBase):
    pass


class ProteinOut(ProteinBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
