from sqlalchemy import Column, String, Integer, DateTime
from ..database import Base

# SQLAlchemy Base Model - represents database table
class QueueSettings(Base):
    __tablename__ = 'queue_settings'
    
    id = Column(String, primary_key=True)
    current_queue_number = Column(Integer, nullable=False, default=0)
    current_referral_code = Column(String, nullable=False, default="")
    next_queue_counter = Column(Integer, nullable=False, default=1)
    periode_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
