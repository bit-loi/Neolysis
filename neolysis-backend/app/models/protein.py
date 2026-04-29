"""
Neolysis — Protein Model
========================
Represents drug target proteins associated with NTDs.
Linked to Disease via disease_id FK.

Fields support both PDB and AlphaFold structure sources.
`sequence` stores the raw FASTA amino acid sequence for future BioLLM embedding.

TODO (BioLLM): Embed protein sequence using ESM-2 or ProtTrans for similarity search.
"""

import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Protein(Base):
    """SQLAlchemy ORM model for a drug target protein."""

    __tablename__ = "proteins"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        index=True,
    )
    name = Column(String(255), nullable=False, index=True)
    pdb_id = Column(String(20), nullable=True, index=True)
    alphafold_id = Column(String(50), nullable=True)
    disease_id = Column(
        UUID(as_uuid=True),
        ForeignKey("diseases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    structure_url = Column(Text, nullable=True)
    sequence = Column(Text, nullable=True)  # Raw FASTA amino acid sequence
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    disease = relationship("Disease", back_populates="proteins")
