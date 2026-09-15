from typing import Dict, Any
from fastapi import APIRouter
from app.services.cache_service import cache_service_instance

router = APIRouter(prefix="/api/cache", tags=["Cache"])

@router.get("/status")
def get_cache_status() -> Dict[str, Any]:
    """Retrieve Redis cache connection state, fallback status, and active key metrics."""
    return cache_service_instance.get_status()
