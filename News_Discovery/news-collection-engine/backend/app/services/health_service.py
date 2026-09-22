from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database.database import ACTIVE_DATABASE_URL
from app.database.models import SourceModel
from app.database.mongodb import mongo_manager
from app.services.cache_service import cache_service_instance
from app.services.qdrant_service import qdrant_service_instance
from app.services.deepseek_service import deepseek_service_instance
from app.utils.logger import get_logger

logger = get_logger("news_engine.health_service")

class HealthService:
    """Engine diagnostic health monitor."""

    @staticmethod
    def get_health_status(db: Session) -> Dict[str, Any]:
        # Database check
        db_status = "connected (SQLite Primary)" if "sqlite" in ACTIVE_DATABASE_URL else "connected"

        # MongoDB status check
        mongo_status = mongo_manager.get_status()

        # Cache check
        cache_status = "connected (Redis)" if cache_service_instance.is_redis_active else "connected (In-Memory fallback)"

        # Available sources count
        avail_sources = db.query(SourceModel).filter(SourceModel.enabled == True).count()

        # Overall health status
        overall_status = "healthy"
        if mongo_status.get("configured") and mongo_status.get("status") not in ["connected"]:
            # MongoDB is configured but currently encountering connection issues
            overall_status = "degraded_mongodb"

        qdrant_status = qdrant_service_instance.get_status()
        deepseek_status = deepseek_service_instance.get_status()

        return {
            "status": overall_status,
            "database": db_status,
            "mongodb": mongo_status,
            "qdrant": qdrant_status,
            "deepseek_r1": deepseek_status,
            "storage_backend": settings.ARTICLE_STORAGE_BACKEND,
            "cache": cache_status,
            "sources_available": avail_sources,
            "demo_mode": settings.DEMO_MODE,
            "environment": settings.ENVIRONMENT
        }
