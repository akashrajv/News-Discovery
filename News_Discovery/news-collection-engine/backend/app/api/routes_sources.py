import uuid
import os
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import SourceModel
from app.schemas.source import SourceRead, SourceCreate
from app.registry.source_registry import SourceRegistry
from app.services.rate_limit_service import RateLimitService
from app.utils.logger import get_logger

logger = get_logger("news_engine.routes_sources")

router = APIRouter(prefix="/api/sources", tags=["Sources"])

@router.get("", response_model=List[SourceRead])
def get_sources(db: Session = Depends(get_db)):
    """Retrieve all registered news collection sources."""
    sources = SourceRegistry.get_all_sources(db)
    result = []
    for s in sources:
        s.next_reset_utc = RateLimitService.get_next_reset_utc(s.last_reset_at)
        result.append(SourceRead.model_validate(s))
    return result

@router.get("/status", response_model=List[Dict[str, Any]])
def get_sources_status(db: Session = Depends(get_db)):
    """Retrieve live status, quota details, rate limit status, and failure history for sources."""
    sources = SourceRegistry.get_all_sources(db)
    result = []
    for s in sources:
        env_key = s.api_key_env_name
        key_configured = bool(os.getenv(env_key)) if env_key else True
        next_reset = RateLimitService.get_next_reset_utc(s.last_reset_at)
        result.append({
            "id": s.id,
            "name": s.name,
            "connection_method": s.connection_method,
            "source_type": s.source_type,
            "status": s.current_status,
            "priority": s.priority,
            "requests_used": s.requests_used,
            "requests_used_today": s.requests_used_today or 0,
            "requests_remaining": s.requests_remaining,
            "last_reset_at": s.last_reset_at.isoformat() if s.last_reset_at else None,
            "next_reset_utc": next_reset.isoformat() if next_reset else None,
            "api_key_configured": key_configured,
            "last_successful_collection": s.last_successful_collection,
            "last_error": s.last_error,
            "estimated_cost": s.estimated_cost_per_request
        })
    return result

@router.post("", response_model=SourceRead)
def add_new_source(source_in: SourceCreate, db: Session = Depends(get_db)):
    """Add a new source dynamically without modifying main collection engine code."""
    new_id = f"src_{uuid.uuid4().hex[:8]}"
    env_key = source_in.api_key_env_name
    key_configured = bool(os.getenv(env_key)) if env_key else (source_in.connection_method == "rss")
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)

    source = SourceModel(
        id=new_id,
        name=source_in.name,
        source_type=source_in.source_type,
        connection_method=source_in.connection_method,
        api_endpoint=source_in.api_endpoint,
        api_key_env_name=source_in.api_key_env_name,
        api_key_configured=key_configured,
        rss_url=source_in.rss_url,
        enabled=source_in.enabled,
        priority=source_in.priority,
        request_limit=source_in.request_limit,
        rate_limit_window_seconds=source_in.rate_limit_window_seconds,
        estimated_cost_per_request=source_in.estimated_cost_per_request,
        requests_used=0,
        requests_used_today=0,
        requests_remaining=source_in.request_limit,
        last_reset_at=today_start,
        current_status="AVAILABLE" if key_configured else "UNAVAILABLE"
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    source.next_reset_utc = RateLimitService.get_next_reset_utc(source.last_reset_at)
    return SourceRead.model_validate(source)
