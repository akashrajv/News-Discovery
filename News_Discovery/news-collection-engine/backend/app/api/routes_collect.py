from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.collection import CollectionRequestInput, CollectionResponse
from app.services.collection_service import CollectionService
from app.utils.logger import get_logger

logger = get_logger("news_engine.routes_collect")

router = APIRouter(prefix="/api", tags=["Collection"])

# Store last routing decision in global memory for quick retrieval
LAST_ROUTING_DECISION = None

@router.post("/collect-news", response_model=CollectionResponse)
async def collect_news(
    request_input: CollectionRequestInput,
    db: Session = Depends(get_db)
):
    """Execute news collection pipeline across configured permitted sources."""
    global LAST_ROUTING_DECISION
    try:
        service = CollectionService(db)
        response = await service.execute_collection(request_input)
        if response.routing_summary:
            LAST_ROUTING_DECISION = response.routing_summary
        return response
    except Exception as e:
        logger.error(f"Collection execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
