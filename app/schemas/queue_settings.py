from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime

class QueueSettingsBase(BaseModel):
    current_queue_number: int = Field(0, ge=0)
    current_referral_code: str = Field("", max_length=10)
    next_queue_counter: int = Field(1, ge=1)
    periode_id: str

class QueueSettingsCreate(QueueSettingsBase):
    pass

class QueueSettingsUpdate(BaseModel):
    current_queue_number: Optional[int] = Field(None, ge=0)
    current_referral_code: Optional[str] = Field(None, max_length=10)
    next_queue_counter: Optional[int] = Field(None, ge=1)

class QueueSettingsResponse(QueueSettingsBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()
    
    class Config:
        from_attributes = True
