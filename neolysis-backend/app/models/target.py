from sqlalchemy import Column, Integer, String, JSON, DateTime, Text
from sqlalchemy.sql import func
from app.db.session import Base

class Target(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    disease = Column(String, index=True)
    organism = Column(String)
    uniprot_id = Column(String, unique=True, index=True)
    alphafold_id = Column(String)
    pdb_id = Column(String)
    # Direct URL to PDB file (R2, AlphaFold, or RCSB) — served to frontend as-is
    pdb_url = Column(Text, nullable=True)
    # Source of the PDB file: "r2" | "alphafold" | "rcsb"
    source = Column(String, nullable=True)
    binding_site_residues = Column(JSON)  # Store residue indices/details
    description = Column(Text)
    asean_prevalence_note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
