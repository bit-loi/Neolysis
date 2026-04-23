from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.db.session import Base


class Paper(Base):
    """
    RAG layer — research papers linked to protein targets.
    Used to ground the LLM narrative in actual literature.
    """
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), index=True, nullable=False)
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
