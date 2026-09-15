from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import ApiUsageModel, CollectionLogModel, ArticleModel, DuplicateRelationshipModel
from app.utils.logger import get_logger

logger = get_logger("news_engine.cost_service")

class CostService:
    """Calculates cost estimates and aggregate usage analytics across collection runs."""

    @staticmethod
    def record_api_usage(
        db: Session,
        source_id: str,
        source_name: str,
        request_count: int,
        estimated_cost: float,
        status: str = "success"
    ):
        usage = ApiUsageModel(
            source_id=source_id,
            source_name=source_name,
            request_count=request_count,
            estimated_cost=estimated_cost,
            status=status
        )
        db.add(usage)
        db.commit()

    @staticmethod
    def get_aggregate_usage(db: Session) -> Dict[str, Any]:
        """Aggregate total collection metrics, API costs, cache hit rates, and duplicate counts."""
        # Total API Cost
        total_cost = db.query(func.sum(ApiUsageModel.estimated_cost)).scalar() or 0.0

        # Collection Logs metrics
        api_requests = db.query(func.count(CollectionLogModel.id)).filter(CollectionLogModel.connector == "api").scalar() or 0
        rss_collections = db.query(func.count(CollectionLogModel.id)).filter(CollectionLogModel.connector == "rss").scalar() or 0
        
        cache_hits = db.query(func.count(CollectionLogModel.id)).filter(CollectionLogModel.cache_hit_or_miss == "hit").scalar() or 0
        cache_misses = db.query(func.count(CollectionLogModel.id)).filter(CollectionLogModel.cache_hit_or_miss == "miss").scalar() or 0

        successful_requests = db.query(func.count(CollectionLogModel.id)).filter(CollectionLogModel.status == "success").scalar() or 0
        failed_requests = db.query(func.count(CollectionLogModel.id)).filter(CollectionLogModel.status == "failed").scalar() or 0

        duplicate_count = db.query(func.count(DuplicateRelationshipModel.id)).scalar() or 0

        total_cache_queries = cache_hits + cache_misses
        cache_hit_rate = round((cache_hits / total_cache_queries * 100), 1) if total_cache_queries > 0 else 0.0

        # Source utilization break-down
        logs = db.query(CollectionLogModel.source_name, func.count(CollectionLogModel.id)).group_by(CollectionLogModel.source_name).all()
        source_utilization = {name: count for name, count in logs}

        return {
            "api_requests": api_requests,
            "rss_collections": rss_collections,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "duplicate_count": duplicate_count,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "estimated_api_cost": round(total_cost, 4),
            "cache_hit_rate": cache_hit_rate,
            "source_utilization": source_utilization
        }
