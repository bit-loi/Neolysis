from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class PaperBase(BaseModel):
    target_id: int
    title: str
    abstract: Optional[str] = None
    source_url: Optional[str] = None


class PaperCreate(PaperBase):
    pass


class PaperOut(PaperBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
