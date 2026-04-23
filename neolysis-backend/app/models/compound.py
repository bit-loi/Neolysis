from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db.session import Base

class Compound(Base):
    __tablename__ = "compounds"

    id = Column(Integer, primary_key=True, index=True)
    pubchem_cid = Column(Integer, unique=True, index=True)
    name = Column(String)
    canonical_smiles = Column(Text)
    molecular_weight = Column(Float)
    logp = Column(Float)
    hbd = Column(Integer)
    hba = Column(Integer)
    qed_score = Column(Float)
    lipinski_pass = Column(Boolean)
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now())

from sqlalchemy import Text # Fix missing import in snippet if needed
