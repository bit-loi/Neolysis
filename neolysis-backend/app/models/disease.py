"""
Neolysis — Disease Model
========================
Represents neglected tropical diseases (NTDs) targeted by the platform.
Covers: Dengue, Leptospirosis, Melioidosis, Scrub Typhus (ASEAN focus).

UUID primary keys are generated server-side via gen_random_uuid() to ensure
safe multi-region insert without collision.
"""

import uuid
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Disease(Base):
    """SQLAlchemy ORM model for a Neglected Tropical Disease."""

    __tablename__ = "diseases"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        index=True,
    )
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    region = Column(String(100), nullable=False, default="ASEAN")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship: one disease → many proteins
    proteins = relationship("Protein", back_populates="disease", lazy="select")
