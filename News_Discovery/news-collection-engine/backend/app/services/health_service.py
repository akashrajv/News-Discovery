from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database.database import ACTIVE_DATABASE_URL
from app.database.models import SourceModel
from app.services.cache_service import cache_service_instance
from app.utils.logger import get_logger

logger = get_logger("news_engine.health_service")

class HealthService:
    """Engine diagnostic health monitor."""

    @staticmethod
    def get_health_status(db: Session) -> Dict[str, Any]:
        # Database check
        db_status = "connected"
        if "sqlite" in ACTIVE_DATABASE_URL:
            db_status = "connected (SQLite fallback)"
        else:
            try:
                db.execute(text("SELECT 1"))
            except Exception:
                db_status = "degraded (SQLite fallback active)"

        # Cache check
        cache_status = "connected (Redis)" if cache_service_instance.is_redis_active else "connected (In-Memory fallback)"

        # Available sources count
        avail_sources = db.query(SourceModel).filter(SourceModel.enabled == True).count()

        return {
            "status": "healthy",
            "database": db_status,
            "cache": cache_status,
            "sources_available": avail_sources,
            "demo_mode": settings.DEMO_MODE,
            "environment": settings.ENVIRONMENT
        }
