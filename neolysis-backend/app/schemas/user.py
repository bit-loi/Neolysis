from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
