from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime

class PeriodeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = False

class PeriodeCreate(PeriodeBase):
    pass

class PeriodeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None

class PeriodeResponse(PeriodeBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()
    
    class Config:
        from_attributes = True
