import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Type
from sqlalchemy.orm import Session

from app.database.models import SourceModel
from app.connectors.base import BaseConnector
from app.connectors.rss_connector import RSSConnector
from app.connectors.newsapi_connector import NewsAPIConnector
from app.connectors.gnews_connector import GNewsConnector
from app.connectors.newsdata_connector import NewsDataConnector
from app.connectors.authorized_feed_connector import AuthorizedFeedConnector
from app.services.rate_limit_service import RateLimitService
from app.utils.logger import get_logger

logger = get_logger("news_engine.source_registry")

DEFAULT_SOURCES = [
    {
        "id": "src_rss_google_news",
        "name": "Google News RSS - India & Global",
        "source_type": "RSS",
        "connection_method": "rss",
        "rss_url": "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en",
        "enabled": True,
        "priority": 10,
        "request_limit": 5000,
        "rate_limit_window_seconds": 86400,
        "estimated_cost_per_request": 0.0,
        "current_status": "AVAILABLE"
    },
    {
        "id": "src_rss_auto_express",
        "name": "Auto Express RSS",
        "source_type": "RSS",
        "connection_method": "rss",
        "rss_url": "https://www.autoexpress.co.uk/feed/all",
        "enabled": True,
        "priority": 8,
        "request_limit": 1000,
        "rate_limit_window_seconds": 86400,
        "estimated_cost_per_request": 0.0,
        "current_status": "AVAILABLE"
    },
    {
        "id": "src_rss_bbc_news",
        "name": "BBC News RSS",
        "source_type": "RSS",
        "connection_method": "rss",
        "rss_url": "http://feeds.bbci.co.uk/news/rss.xml",
        "enabled": True,
        "priority": 8,
        "request_limit": 1000,
        "rate_limit_window_seconds": 86400,
        "estimated_cost_per_request": 0.0,
        "current_status": "AVAILABLE"
    },
    {
        "id": "src_newsapi",
        "name": "NewsAPI",
        "source_type": "API",
        "connection_method": "api",
        "api_endpoint": "https://newsapi.org/v2/everything",
        "api_key_env_name": "NEWSAPI_KEY",
        "enabled": True,
        "priority": 6,
        "request_limit": 100,
        "rate_limit_window_seconds": 86400,
        "estimated_cost_per_request": 0.001,
        "current_status": "AVAILABLE"
    },
    {
        "id": "src_gnews",
        "name": "GNews.io",
        "source_type": "API",
        "connection_method": "api",
        "api_endpoint": "https://gnews.io/api/v4/search",
        "api_key_env_name": "GNEWS_API_KEY",
        "enabled": True,
        "priority": 5,
        "request_limit": 100,
        "rate_limit_window_seconds": 86400,
        "estimated_cost_per_request": 0.001,
        "current_status": "AVAILABLE"
    },
    {
        "id": "src_newsdata",
        "name": "NewsData.io",
        "source_type": "API",
        "connection_method": "api",
        "api_endpoint": "https://newsdata.io/api/1/news",
        "api_key_env_name": "NEWSDATA_API_KEY",
        "enabled": True,
        "priority": 4,
        "request_limit": 200,
        "rate_limit_window_seconds": 86400,
        "estimated_cost_per_request": 0.0005,
        "current_status": "AVAILABLE"
    }
]

CONNECTOR_MAPPING: Dict[str, Type[BaseConnector]] = {
    "src_rss_google_news": RSSConnector,
    "src_rss_auto_express": RSSConnector,
    "src_rss_bbc_news": RSSConnector,
    "src_newsapi": NewsAPIConnector,
    "src_gnews": GNewsConnector,
    "src_newsdata": NewsDataConnector,
    "rss": RSSConnector,
    "api": NewsAPIConnector,
    "authorized_feed": AuthorizedFeedConnector
}

class SourceRegistry:
    """Registry to load, manage, and instantiate source connectors dynamically."""

    @staticmethod
    def initialize_default_sources(db: Session):
        """Seed default sources into database if missing."""
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        for src_data in DEFAULT_SOURCES:
            existing = db.query(SourceModel).filter(SourceModel.id == src_data["id"]).first()
            if existing:
                if existing.id == "src_rss_google_news" and ("Tata+Motors" in (existing.rss_url or "") or "{query}" not in (existing.rss_url or "")):
                    existing.rss_url = src_data["rss_url"]
                    existing.name = src_data["name"]
                    existing.priority = src_data["priority"]
                if existing.last_reset_at is None:
                    existing.last_reset_at = today_start
                    existing.requests_used_today = existing.requests_used_today or 0
            else:
                env_key = src_data.get("api_key_env_name")
                key_configured = bool(os.getenv(env_key)) if env_key else False
                
                source = SourceModel(
                    id=src_data["id"],
                    name=src_data["name"],
                    source_type=src_data["source_type"],
                    connection_method=src_data["connection_method"],
                    api_endpoint=src_data.get("api_endpoint"),
                    api_key_env_name=src_data.get("api_key_env_name"),
                    api_key_configured=key_configured,
                    rss_url=src_data.get("rss_url"),
                    enabled=src_data.get("enabled", True),
                    priority=src_data.get("priority", 5),
                    request_limit=src_data.get("request_limit", 100),
                    rate_limit_window_seconds=src_data.get("rate_limit_window_seconds", 86400),
                    estimated_cost_per_request=src_data.get("estimated_cost_per_request", 0.0),
                    requests_used=0,
                    requests_used_today=0,
                    requests_remaining=src_data.get("request_limit", 100),
                    last_reset_at=today_start,
                    current_status="AVAILABLE" if (src_data["connection_method"] == "rss" or key_configured) else "UNAVAILABLE"
                )
                db.add(source)
        db.commit()

    @staticmethod
    def get_all_sources(db: Session) -> List[SourceModel]:
        """Fetch all registered sources from database and evaluate quota reset status."""
        sources = db.query(SourceModel).all()
        # Evaluate daily quota resets and dynamic api_key_configured status
        for s in sources:
            RateLimitService.check_and_reset_quota(db, s)
            if s.api_key_env_name:
                is_cfg = bool(os.getenv(s.api_key_env_name))
                s.api_key_configured = is_cfg
                if is_cfg and s.current_status == "UNAVAILABLE":
                    s.current_status = "AVAILABLE"
                elif not is_cfg and s.connection_method == "api" and s.current_status == "AVAILABLE":
                    s.current_status = "UNAVAILABLE"
        return sources

    @staticmethod
    def get_connector(source_model: SourceModel) -> BaseConnector:
        """Instantiate appropriate connector class for a source model."""
        source_dict = {
            "id": source_model.id,
            "name": source_model.name,
            "source_type": source_model.source_type,
            "connection_method": source_model.connection_method,
            "api_endpoint": source_model.api_endpoint,
            "api_key_env_name": source_model.api_key_env_name,
            "rss_url": source_model.rss_url,
            "enabled": source_model.enabled,
            "priority": source_model.priority,
            "request_limit": source_model.request_limit,
            "rate_limit_window_seconds": source_model.rate_limit_window_seconds,
            "estimated_cost_per_request": source_model.estimated_cost_per_request,
            "requests_used": source_model.requests_used,
            "requests_remaining": source_model.requests_remaining,
            "current_status": source_model.current_status
        }

        # Check explicit ID mapping first
        if source_model.id in CONNECTOR_MAPPING:
            connector_cls = CONNECTOR_MAPPING[source_model.id]
        elif source_model.connection_method.lower() in CONNECTOR_MAPPING:
            connector_cls = CONNECTOR_MAPPING[source_model.connection_method.lower()]
        else:
            connector_cls = RSSConnector if source_model.connection_method.lower() == "rss" else BaseConnector

        return connector_cls(source_dict)
