from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class WargaBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    kk_number: str = Field(..., min_length=16, max_length=16)
    rt_rw: str = Field(..., min_length=1, max_length=50)
    periode_id: str

class WargaCreate(WargaBase):
    pass

class WargaUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    kk_number: Optional[str] = Field(None, min_length=16, max_length=16)
    rt_rw: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[str] = Field(None, pattern=r'^(waiting|serving|served|pending)$')

class WargaResponse(BaseModel):
    id: str
    name: str
    kk_number: str
    rt_rw: str
    referral_code: str
    queue_number: int
    status: str
    created_at: str
    updated_at: str
    periode_id: str
    
    class Config:
        from_attributes = True
