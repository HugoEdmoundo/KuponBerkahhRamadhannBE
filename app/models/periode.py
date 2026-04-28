from sqlalchemy import Column, String, Boolean, DateTime
from ..database import Base

# SQLAlchemy Base Model - represents database table
class Periode(Base):
    __tablename__ = 'periodes'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
