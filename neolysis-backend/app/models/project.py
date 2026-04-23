from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.db.session import Base
from sqlalchemy.orm import relationship

class SavedProject(Base):
    __tablename__ = "saved_projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
