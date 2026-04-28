from sqlalchemy import Column, String, Integer, DateTime
from ..database import Base

# SQLAlchemy Base Model - represents database table
class Warga(Base):
    __tablename__ = 'warga'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    kk_number = Column(String, nullable=False)
    rt_rw = Column(String, nullable=False)
    referral_code = Column(String, nullable=False)
    queue_number = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    periode_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
