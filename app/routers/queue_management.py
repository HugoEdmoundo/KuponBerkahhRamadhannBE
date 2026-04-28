from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db_session, get_current_time
from ..models.warga import Warga
from ..schemas.warga import WargaResponse
from ..models.queue_settings import QueueSettings
from ..models.periode import Periode
from ..exceptions import NotFoundError, DatabaseError, BadRequestError

router = APIRouter(prefix="/queue", tags=["queue-management"])


def get_active_periode(db: Session) -> Periode:
    """Get the active periode"""
    periode = db.query(Periode).filter(Periode.is_active == True).first()
    if not periode:
        raise BadRequestError("No active periode found")
    return periode


def get_queue_settings_for_periode(periode_id: str, db: Session) -> QueueSettings:
    """Get queue settings for a periode"""
    settings = db.query(QueueSettings).filter(QueueSettings.periode_id == periode_id).first()
    if not settings:
        raise NotFoundError("Queue settings not found for active periode")
    return settings


@router.post("/next", response_model=dict)
def handle_next_queue(db: Session = Depends(get_db_session)):
    """
    Handle next queue operation:
    1. Change current serving to served
    2. Change first waiting to serving
    3. Update queue settings
    """
    try:
        periode = get_active_periode(db)
        queue_settings = get_queue_settings_for_periode(periode.id, db)
        
        # Find current serving
        current_serving = db.query(Warga).filter(
            Warga.periode_id == periode.id,
            Warga.status == "serving"
        ).first()
        
        # Mark current serving as served
        if current_serving:
            current_serving.status = "served"
        
        # Find first waiting
        first_waiting = db.query(Warga).filter(
            Warga.periode_id == periode.id,
            Warga.status == "waiting"
        ).order_by(Warga.queue_number).first()
        
        if first_waiting:
            # Mark as serving
            first_waiting.status = "serving"
            
            # Update queue settings
            queue_settings.current_queue_number = first_waiting.queue_number
            queue_settings.current_referral_code = first_waiting.referral_code
            
            db.commit()
            
            return {
                "message": "Queue advanced successfully",
                "current_serving": {
                    "id": str(first_waiting.id),
                    "name": first_waiting.name,
                    "queue_number": first_waiting.queue_number,
                    "referral_code": first_waiting.referral_code
                },
                "previous_serving": {
                    "id": str(current_serving.id) if current_serving else None,
                    "name": current_serving.name if current_serving else None
                }
            }
        else:
            # No waiting queue, reset current serving
            queue_settings.current_queue_number = 0
            queue_settings.current_referral_code = ""
            db.commit()
            
            return {
                "message": "No waiting customers to serve",
                "data": None,
                "current_serving": None,
                "previous_serving": {
                    "id": str(current_serving.id) if current_serving else None,
                    "name": current_serving.name if current_serving else None
                }
            }
    except (NotFoundError, BadRequestError):
        raise
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Failed to advance queue: {str(e)}")
    finally:
        db.close()


@router.post("/pending", response_model=dict)
def handle_pending_queue(db: Session = Depends(get_db_session)):
    """
    Handle pending operation:
    1. Change current serving to pending
    2. Call first waiting as serving
    3. Update queue settings
    """
    try:
        periode = get_active_periode(db)
        queue_settings = get_queue_settings_for_periode(periode.id, db)
        
        # Find current serving
        current_serving = db.query(Warga).filter(
            Warga.periode_id == periode.id,
            Warga.status == "serving"
        ).first()
        
        if not current_serving:
            raise NotFoundError("No current serving to mark as pending")
        
        # Mark current serving as pending
        current_serving.status = "pending"
        
        # Find first waiting
        first_waiting = db.query(Warga).filter(
            Warga.periode_id == periode.id,
            Warga.status == "waiting"
        ).order_by(Warga.queue_number).first()
        
        if first_waiting:
            # Mark as serving
            first_waiting.status = "serving"
            
            # Update queue settings
            queue_settings.current_queue_number = first_waiting.queue_number
            queue_settings.current_referral_code = first_waiting.referral_code
            
            db.commit()
            
            return {
                "message": "Queue handled pending successfully",
                "current_serving": {
                    "id": str(first_waiting.id),
                    "name": first_waiting.name,
                    "queue_number": first_waiting.queue_number,
                    "referral_code": first_waiting.referral_code
                },
                "pending": {
                    "id": str(current_serving.id),
                    "name": current_serving.name,
                    "queue_number": current_serving.queue_number,
                    "referral_code": current_serving.referral_code
                }
            }
        else:
            # No waiting queue, reset current serving
            queue_settings.current_queue_number = 0
            queue_settings.current_referral_code = ""
            db.commit()
            
            return {
                "message": "Current serving marked as pending, no waiting queue",
                "current_serving": None,
                "pending": {
                    "id": str(current_serving.id),
                    "name": current_serving.name,
                    "queue_number": current_serving.queue_number,
                    "referral_code": current_serving.referral_code
                }
            }
    except (NotFoundError, BadRequestError):
        raise
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Failed to handle pending queue: {str(e)}")
    finally:
        db.close()


@router.post("/back", response_model=dict)
def handle_back_queue(db: Session = Depends(get_db_session)):
    """
    Handle back operation:
    1. Change current serving to waiting
    2. Get last served as serving
    3. Update queue settings
    """
    try:
        periode = get_active_periode(db)
        queue_settings = get_queue_settings_for_periode(periode.id, db)
        
        # Find current serving
        current_serving = db.query(Warga).filter(
            Warga.periode_id == periode.id,
            Warga.status == "serving"
        ).first()
        
        if not current_serving:
            # raise NotFoundError("No current serving to go back")
            if not current_serving:
                last_served = db.query(Warga).filter(
                    Warga.periode_id == periode.id,
                    Warga.status == "served"
                ).order_by(Warga.queue_number.desc()).first()

                if last_served:
                    last_served.status = "serving"
                    queue_settings.current_queue_number = last_served.queue_number
                    queue_settings.current_referral_code = last_served.referral_code
                    db.commit()
                    return {
                        "message": "Queue back operation successful (fallback)",
                        "current_serving": {
                            "id": str(last_served.id),
                            "name": last_served.name,
                            "queue_number": last_served.queue_number,
                            "referral_code": last_served.referral_code
                        },
                        "previous_serving": None
                    }
                else:
                    return {
                        "message": "No queue available to back",
                        "data": None
                    }

        
        # Mark current serving as waiting
        current_serving.status = "waiting"
        
        # Find last served
        last_served = db.query(Warga).filter(
            Warga.periode_id == periode.id,
            Warga.status == "served"
        ).order_by(Warga.queue_number.desc()).first()
        
        if last_served:
            # Mark as serving
            last_served.status = "serving"
            
            # Update queue settings
            queue_settings.current_queue_number = last_served.queue_number
            queue_settings.current_referral_code = last_served.referral_code
            
            db.commit()
            
            return {
                "message": "Queue back operation successful",
                "current_serving": {
                    "id": str(last_served.id),
                    "name": last_served.name,
                    "queue_number": last_served.queue_number,
                    "referral_code": last_served.referral_code
                },
                "previous_serving": {
                    "id": str(current_serving.id),
                    "name": current_serving.name,
                    "queue_number": current_serving.queue_number,
                    "referral_code": current_serving.referral_code
                }
            }
        else:
            # No served queue, reset current serving
            queue_settings.current_queue_number = 0
            queue_settings.current_referral_code = ""
            db.commit()
            
            return {
                "message": "No served customers to call back",
                "data": None,
                "current_serving": None,
                "previous_serving": {
                    "id": str(current_serving.id),
                    "name": current_serving.name,
                    "queue_number": current_serving.queue_number,
                    "referral_code": current_serving.referral_code
                }
            }
    except (NotFoundError, BadRequestError):
        raise
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Failed to handle back queue: {str(e)}")
    finally:
        db.close()


@router.get("/status", response_model=dict)
def get_queue_status(db: Session = Depends(get_db_session)):
    """Get current queue status"""
    try:
        periode = get_active_periode(db)
        
        try:
            queue_settings = get_queue_settings_for_periode(periode.id, db)
        except NotFoundError:
            return {
                "message": "No queue settings found for active periode",
                "data": None
            }
        
        # Get current serving
        current_serving = db.query(Warga).filter(
            Warga.periode_id == periode.id,
            Warga.status == "serving"
        ).first()
        
        # Get queue counts
        waiting_count = db.query(Warga).filter(
            Warga.periode_id == periode.id,
            Warga.status == "waiting"
        ).count()
        
        served_count = db.query(Warga).filter(
            Warga.periode_id == periode.id,
            Warga.status == "served"
        ).count()
        
        pending_count = db.query(Warga).filter(
            Warga.periode_id == periode.id,
            Warga.status == "pending"
        ).count()
        
        return {
            "periode": {
                "id": str(periode.id),
                "name": periode.name
            },
            "queue_settings": {
                "current_queue_number": queue_settings.current_queue_number,
                "current_referral_code": queue_settings.current_referral_code,
                "next_queue_counter": queue_settings.next_queue_counter
            },
            "current_serving": {
                "id": str(current_serving.id) if current_serving else None,
                "name": current_serving.name if current_serving else None,
                "queue_number": current_serving.queue_number if current_serving else None,
                "referral_code": current_serving.referral_code if current_serving else None
            },
            "statistics": {
                "waiting": waiting_count,
                "serving": 1 if current_serving else 0,
                "served": served_count,
                "pending": pending_count,
                "total": waiting_count + (1 if current_serving else 0) + served_count + pending_count
            }
        }
    except (NotFoundError, BadRequestError):
        raise
    except Exception as e:
        raise DatabaseError(f"Failed to get queue status: {str(e)}")
    finally:
        db.close()
