from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db_session, get_current_time
from ..models.queue_settings import QueueSettings
from ..schemas.queue_settings import QueueSettingsCreate, QueueSettingsResponse
from ..models.periode import Periode
from ..exceptions import NotFoundError, DatabaseError
import uuid

router = APIRouter(prefix="/queue-settings")


@router.get("/periode/{periode_id}", response_model=QueueSettingsResponse)
def get_queue_settings_by_periode(periode_id: str, db: Session = Depends(get_db_session)):
    try:
        settings = db.query(QueueSettings).filter(QueueSettings.periode_id == periode_id).first()
        if not settings:
            raise NotFoundError(f"Queue settings not found for periode {periode_id}")
        return QueueSettingsResponse.model_validate(settings.__dict__)
    except NotFoundError:
        raise
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve queue settings: {str(e)}")
    finally:
        db.close()


@router.post("", response_model=QueueSettingsResponse, status_code=201)
def create_queue_settings(data: QueueSettingsCreate, db: Session = Depends(get_db_session)):
    try:
        # Check if periode exists
        periode = db.query(Periode).filter(Periode.id == data.periode_id).first()
        if not periode:
            raise NotFoundError(f"Periode with id {data.periode_id} not found")
        
        # Check if queue settings already exist
        existing = db.query(QueueSettings).filter(QueueSettings.periode_id == data.periode_id).first()
        if existing:
            raise DatabaseError(f"Queue settings already exist for periode {data.periode_id}")
        
        settings_id = str(uuid.uuid4())
        now = get_current_time()
        
        new_settings = QueueSettings(
            id=settings_id,
            current_queue_number=data.current_queue_number,
            current_referral_code=data.current_referral_code,
            next_queue_counter=data.next_queue_counter,
            periode_id=data.periode_id,
            created_at=now,
            updated_at=now
        )
        
        db.add(new_settings)
        db.commit()
        db.refresh(new_settings)
        
        return QueueSettingsResponse.model_validate(new_settings.__dict__)
    except NotFoundError:
        raise
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(f"Failed to create queue settings: {str(e)}")
    finally:
        db.close()
