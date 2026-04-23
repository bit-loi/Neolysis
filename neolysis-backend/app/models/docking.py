from sqlalchemy import Column, Integer, Float, JSON, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from app.db.session import Base

class DockingResult(Base):
    __tablename__ = "docking_results"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), index=True)
    compound_id = Column(Integer, ForeignKey("compounds.id"), index=True)
    vina_score_kcal_mol = Column(Float)
    binding_pose_json = Column(JSON)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String)  # e.g., "precomputed" or "live_batch"
