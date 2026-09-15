from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.health_service import HealthService

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("")
def get_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve engine health, database connection, cache status, and available sources."""
    return HealthService.get_health_status(db)
