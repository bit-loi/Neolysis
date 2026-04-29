"""
Neolysis — Pydantic Schemas for Knowledge Graph
================================================
RDF-style triple schemas. Supports subject/relation/object query patterns.

Example triple:
    { "subject": "Dengue NS5", "relation": "inhibited_by", "object": "Quercetin",
      "source": "DrugBank", "confidence": 0.92 }
"""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class KnowledgeGraphBase(BaseModel):
    subject: str = Field(..., max_length=255, description="Entity being described (e.g. protein name)")
    relation: str = Field(..., max_length=100, description="Relationship type (e.g. 'inhibited_by')")
    object: str = Field(..., max_length=255, description="Target entity (e.g. compound name)")
    source: Optional[str] = Field(None, max_length=255, description="Data source (e.g. DrugBank)")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score 0–1")


class KnowledgeGraphCreate(KnowledgeGraphBase):
    pass


class KnowledgeGraphOut(KnowledgeGraphBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeGraphListResponse(BaseModel):
    """Paginated list of knowledge graph triples."""
    total: int
    items: List[KnowledgeGraphOut]
