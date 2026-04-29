"""
Neolysis Disease Schema (fixed — no circular import)
=====================================================
Pydantic v2 schemas for Disease model.
The DiseaseWithProteins variant is assembled lazily to avoid circular imports.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DiseaseBase(BaseModel):
    name: str = Field(..., max_length=255, description="Disease name, e.g. 'Dengue Fever'")
    description: Optional[str] = Field(None, description="Clinical description")
    region: str = Field("ASEAN", max_length=100, description="Geographic region")


class DiseaseCreate(DiseaseBase):
    pass


class DiseaseOut(DiseaseBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiseaseWithProteins(DiseaseOut):
    """Disease detail response including its associated protein targets."""

    # Use forward-ref string to avoid circular imports at definition time
    proteins: List[dict] = []

    model_config = ConfigDict(from_attributes=True)
