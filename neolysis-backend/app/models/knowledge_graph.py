"""
Neolysis — Knowledge Graph Model
=================================
Stores biomedical knowledge as RDF-style triples:
    subject → relation → object

Examples:
    "Dengue NS5"  → "inhibited_by"       → "Quercetin"
    "NS3_Helicase"→ "associated_with"    → "Dengue Fever"
    "Quercetin"   → "targets"            → "LipL32"

Sources: DrugBank, UniProt, literature extraction, manual curation.

TODO (GNN): Replace confidence scoring with a Graph Neural Network
            trained on DrugBank/KEGG interaction graph.
"""

import uuid
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base


class KnowledgeGraph(Base):
    """SQLAlchemy ORM model for a biomedical knowledge graph triple."""

    __tablename__ = "knowledge_graph"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        index=True,
    )
    subject = Column(String(255), nullable=False, index=True)
    relation = Column(String(100), nullable=False, index=True)
    object = Column(String(255), nullable=False, index=True)
    source = Column(String(255), nullable=True)   # e.g. "DrugBank", "PubMed:12345678"
    confidence = Column(Float, nullable=True)      # 0.0 – 1.0
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
