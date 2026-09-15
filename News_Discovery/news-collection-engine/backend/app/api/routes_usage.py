from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.usage import UsageSummaryRead
from app.services.cost_service import CostService

router = APIRouter(prefix="/api/usage", tags=["Usage"])

@router.get("", response_model=UsageSummaryRead)
def get_usage(db: Session = Depends(get_db)):
    """Retrieve usage analytics, API request counts, cache hit rates, and estimated costs."""
    data = CostService.get_aggregate_usage(db)
    return UsageSummaryRead.model_validate(data)
