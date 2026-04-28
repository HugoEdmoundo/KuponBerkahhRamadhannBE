from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db_session, get_current_time
from ..models.periode import Periode
from ..schemas.periode import PeriodeCreate, PeriodeUpdate, PeriodeResponse
from ..exceptions import NotFoundError, DatabaseError
import uuid

router = APIRouter()

@router.get("/periodes", response_model=list[PeriodeResponse])
def get_periodes(db: Session = Depends(get_db_session)):
    try:
        periodes = db.query(Periode).all()
        return [PeriodeResponse.model_validate(p.__dict__) for p in periodes]
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve periodes: {str(e)}")
    finally:
        db.close()

@router.get("/periodes/active")
def get_active_periode_endpoint(db: Session = Depends(get_db_session)):
    try:
        active_periode = db.query(Periode).filter(Periode.is_active == True).first()
        if not active_periode:
            return {"message": "No active periode found", "data": None}
        
        return {"message": "Active periode found", "data": PeriodeResponse.model_validate(active_periode.__dict__)}
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve active periode: {str(e)}")
    finally:
        db.close()

@router.post("/periodes", response_model=PeriodeResponse, status_code=201)
def create_periode(data: PeriodeCreate, db: Session = Depends(get_db_session)):
    try:
        # Deactivate all other periodes
        db.query(Periode).filter(Periode.is_active == True).update({Periode.is_active: False})
        
        periode_id = str(uuid.uuid4())
        now = get_current_time()
        
        new_periode = Periode(
            id=periode_id,
            name=data.name,
            is_active=data.is_active,
            created_at=now,
            updated_at=now
        )
        
        db.add(new_periode)
        db.commit()
        db.refresh(new_periode)
        
        return PeriodeResponse.model_validate(new_periode.__dict__)
    except Exception as e:
        raise DatabaseError(f"Failed to create periode: {str(e)}")
    finally:
        db.close()

@router.patch("/periodes/{periode_id}/activate", response_model=PeriodeResponse)
def activate_periode(periode_id: str, db: Session = Depends(get_db_session)):
    try:
        # Deactivate all periodes
        db.query(Periode).filter(Periode.is_active == True).update({Periode.is_active: False})
        
        # Activate the specified periode
        periode = db.query(Periode).filter(Periode.id == periode_id).first()
        if not periode:
            raise NotFoundError(f"Periode with id {periode_id} not found")
        
        periode.is_active = True
        periode.updated_at = get_current_time()
        
        db.commit()
        db.refresh(periode)
        
        return PeriodeResponse.model_validate(periode.__dict__)
    except Exception as e:
        raise DatabaseError(f"Failed to activate periode: {str(e)}")
    finally:
        db.close()

@router.patch("/{periode_id}", response_model=PeriodeResponse)
def update_periode(periode_id: str, data: PeriodeUpdate, db: Session = Depends(get_db_session)):
    try:
        periode = db.query(Periode).filter(Periode.id == periode_id).first()
        if not periode:
            raise NotFoundError(f"Periode with id {periode_id} not found")
        
        # If activating this periode, deactivate others first
        if data.is_active == True:
            db.query(Periode).filter(Periode.is_active == True).update({Periode.is_active: False})
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        update_data['updated_at'] = get_current_time()
        
        for field, value in update_data.items():
            if hasattr(periode, field):
                setattr(periode, field, value)
        
        db.commit()
        db.refresh(periode)
        
        return PeriodeResponse.model_validate(periode.__dict__)
    except Exception as e:
        raise DatabaseError(f"Failed to update periode: {str(e)}")
    finally:
        db.close()

@router.delete("/{periode_id}")
def delete_periode(periode_id: str, db: Session = Depends(get_db_session)):
    try:
        periode = db.query(Periode).filter(Periode.id == periode_id).first()
        if not periode:
            raise NotFoundError(f"Periode with id {periode_id} not found")
        
        db.delete(periode)
        db.commit()
        
        return {"message": "Periode deleted successfully"}
    except Exception as e:
        raise DatabaseError(f"Failed to delete periode: {str(e)}")
    finally:
        db.close()