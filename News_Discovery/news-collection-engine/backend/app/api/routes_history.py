from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import CollectionRequestModel
from app.schemas.collection import CollectionHistoryRead

router = APIRouter(prefix="/api/collection-history", tags=["History"])

@router.get("", response_model=List[CollectionHistoryRead])
def get_collection_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve history of user collection requests with request parameters and summary metrics."""
    records = db.query(CollectionRequestModel).order_by(CollectionRequestModel.created_at.desc()).limit(limit).all()
    return [CollectionHistoryRead.model_validate(r) for r in records]
