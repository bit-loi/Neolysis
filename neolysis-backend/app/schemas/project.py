from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    target_id: int

class ProjectCreate(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    id: int
    user_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
