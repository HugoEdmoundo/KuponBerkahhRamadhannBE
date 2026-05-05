import sqlite3, uuid, random, string
from datetime import datetime
import pytz
from typing import Optional, Dict
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text

def init_database():
    """Initialize database with SQLAlchemy Base models"""
    # Import models supaya terdaftar ke Base.metadata
    from app.models.periode import Periode
    from app.models.warga import Warga
    from app.models.queue_settings import QueueSettings
    
    Base.metadata.create_all(bind=engine)

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_current_time():
    """Get current datetime as Python datetime object"""
    return datetime.now(pytz.timezone('Asia/Jakarta'))

# SQLAlchemy setup with connection pool settings
engine = create_engine(
    'sqlite:///queue.db',
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db_session() -> Session:
    """Get SQLAlchemy session"""
    return SessionLocal()

def get_active_periode_orm(db: Session):
    """Get active periode using SQLAlchemy"""
    from ..models.periode import Periode
    return db.query(Periode).filter(Periode.is_active == True).first()

def get_queue_settings_orm(db: Session, periode_id: str):
    """Get queue settings using SQLAlchemy"""
    from ..models.queue_settings import QueueSettings
    return db.query(QueueSettings).filter(QueueSettings.periode_id == periode_id).first()

