from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from ..database import get_db_session, get_current_time, generate_referral_code
from ..websocket import broadcast_websocket
from ..models.warga import Warga
from ..schemas.warga import WargaCreate, WargaUpdate, WargaResponse
from ..models.queue_settings import QueueSettings
from ..exceptions import NotFoundError, DatabaseError
import uuid
import json
from typing import Optional

router = APIRouter()

@router.get("/registrations", response_model=list[WargaResponse])
def get_registrations(
    periodeId: Optional[str] = Query(None, description="Filter by periode ID"), 
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db_session)
):
    try:
        query = db.query(Warga)
        if periodeId:
            query = query.filter(Warga.periode_id == periodeId)
        
        if status:
            if status not in ['waiting', 'serving', 'served', 'pending']:
                raise DatabaseError(f"Invalid status: {status}. Must be: waiting, serving, served, or pending")
            query = query.filter(Warga.status == status)
        
        registrations = query.order_by(Warga.queue_number).all()
        return [WargaResponse.model_validate(r.__dict__) for r in registrations]
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve registrations: {str(e)}")
    finally:
        db.close()

@router.post("/registrations", response_model=WargaResponse, status_code=201)
def create_registration(data: WargaCreate, db: Session = Depends(get_db_session)):
    try:
        # Verify periode exists
        from ..models.periode import Periode
        periode = db.query(Periode).filter(Periode.id == data.periode_id).first()
        if not periode:
            raise NotFoundError(f"Periode with id {data.periode_id} not found")
        
        # Get queue settings
        settings = db.query(QueueSettings).filter(QueueSettings.periode_id == data.periode_id).first()
        next_queue = settings.next_queue_counter if settings else 1
        
        # Generate unique referral code
        referral_code = generate_referral_code()
        while db.query(Warga).filter(Warga.referral_code == referral_code).first():
            referral_code = generate_referral_code()
        
        registration_id = str(uuid.uuid4())
        now = get_current_time()
        
        new_registration = Warga(
            id=registration_id,
            name=data.name,
            kk_number=data.kk_number,
            rt_rw=data.rt_rw,
            referral_code=referral_code,
            queue_number=next_queue,
            status="waiting",
            created_at=now,
            updated_at=now,
            periode_id=data.periode_id
        )
        
        db.add(new_registration)
        
        # Update queue settings
        if settings:
            settings.next_queue_counter += 1
        else:
            settings = QueueSettings(
                id=str(uuid.uuid4()),
                current_queue_number=0,
                current_referral_code="",
                next_queue_counter=next_queue + 1,
                periode_id=data.periode_id,
                created_at=now,
                updated_at=now
            )
            db.add(settings)
        
        db.commit()
        db.refresh(new_registration)
        
        broadcast_websocket(json.dumps({
            "type": "registration_created",
            "data": {
                "id": registration_id,
                "name": data.name,
                "queue_number": next_queue,
                "referral_code": referral_code,
                "status": "waiting",
                "periode_id": data.periode_id
            }
        }))
        
        return WargaResponse.model_validate(new_registration.__dict__)
    except NotFoundError:
        raise
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(f"Failed to create registration: {str(e)}")
    finally:
        db.close()

@router.patch("/registrations/{registration_id}", response_model=WargaResponse)
def update_registration(registration_id: str, data: WargaUpdate, db: Session = Depends(get_db_session)):
    try:
        registration = db.query(Warga).filter(Warga.id == registration_id).first()
        if not registration:
            raise NotFoundError(f"Registration with id {registration_id} not found")
        
        if data.status and data.status not in ['waiting', 'serving', 'served', 'pending']:
            raise DatabaseError(f"Invalid status: {data.status}. Must be: waiting, serving, served, or pending")
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        update_data['updated_at'] = get_current_time()
        
        for field, value in update_data.items():
            if hasattr(registration, field):
                setattr(registration, field, value)
        
        db.commit()
        db.refresh(registration)
        
        return WargaResponse.model_validate(registration.__dict__)
    except Exception as e:
        raise DatabaseError(f"Failed to update registration: {str(e)}")
    finally:
        db.close()

@router.delete("/registrations/{registration_id}")
def delete_registration(registration_id: str, db: Session = Depends(get_db_session)):
    try:
        registration = db.query(Warga).filter(Warga.id == registration_id).first()
        if not registration:
            raise NotFoundError(f"Registration with id {registration_id} not found")
        
        db.delete(registration)
        db.commit()
        
        return {"message": "Registration deleted successfully"}
    except Exception as e:
        raise DatabaseError(f"Failed to delete registration: {str(e)}")
    finally:
        db.close()
    