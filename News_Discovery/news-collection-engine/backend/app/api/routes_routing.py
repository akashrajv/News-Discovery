from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from app.api.routes_collect import LAST_ROUTING_DECISION

router = APIRouter(prefix="/api/routing", tags=["Routing"])

@router.get("/last-decision")
def get_last_routing_decision() -> Optional[Dict[str, Any]]:
    """Retrieve detailed routing evaluation decision from the last collection request."""
    if not LAST_ROUTING_DECISION:
        return {
            "message": "No collection request executed yet.",
            "selected_sources": [],
            "skipped_sources": []
        }
    return LAST_ROUTING_DECISION
