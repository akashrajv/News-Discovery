from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import httpx

from app.connectors.base import BaseConnector
from app.schemas.article import ArticleCreate
from app.utils.text_utils import normalize_url, normalize_title, compute_content_hash
from app.utils.logger import get_logger

logger = get_logger("news_engine.authorized_feed")

class AuthorizedFeedConnector(BaseConnector):
    """Connector for authorized JSON feeds or publisher endpoints."""

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.feed_url = source_config.get("api_endpoint") or source_config.get("rss_url")

    def validate_configuration(self) -> Tuple[bool, Optional[str]]:
        if not self.feed_url:
            return False, "Authorized feed URL endpoint is missing"
        return True, None

    def is_available(self) -> Tuple[bool, str]:
        valid, msg = self.validate_configuration()
        if not valid:
            return False, msg or "Configuration invalid"
        if not self.source_config.get("enabled", True):
            return False, "Source is disabled"
        return True, "Available (Authorized Feed)"

    def build_query(self, entity: str, keywords: List[str], location: Optional[str] = None, category: Optional[str] = None) -> str:
        return f"{entity} {' '.join(keywords)}".strip()

    async def fetch(self, query: str, time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        avail, msg = self.is_available()
        if not avail:
            return []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.feed_url, headers={"User-Agent": "NewsCollectionEngine/1.0"})
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return data.get("items") or data.get("articles") or data.get("data") or []
                return []
        except Exception as e:
            logger.error(f"Error fetching authorized feed {self.feed_url}: {e}")
            return []

    def normalize(self, raw_items: List[Dict[str, Any]]) -> List[ArticleCreate]:
        normalized = []
        for item in raw_items:
            title = (item.get("title") or item.get("headline") or "").strip()
            if not title:
                continue

            url = (item.get("url") or item.get("link") or "").strip()
            description = item.get("description") or item.get("summary")
            content = item.get("content") or item.get("body")
            source_name = item.get("source") or self.source_name
            published_str = item.get("published_at") or item.get("date")

            published_dt = None
            pub_unavailable = False
            if published_str:
                try:
                    published_dt = datetime.fromisoformat(str(published_str).replace("Z", "+00:00"))
                except Exception:
                    pub_unavailable = True
            else:
                pub_unavailable = True

            author = (item.get("author") or item.get("byline") or "").strip() or None

            norm_url = normalize_url(url)
            norm_t = normalize_title(title)
            c_hash = compute_content_hash(title, description)

            article = ArticleCreate(
                title=title,
                description=description,
                content=content,
                source=source_name,
                author=author,
                published_at=published_dt,
                url=url or f"https://authorized.feed/article/{c_hash}",
                category=self.source_config.get("category"),
                location=self.source_config.get("location"),
                collection_method="authorized_feed",
                canonical_url=norm_url,
                normalized_title=norm_t,
                content_hash=c_hash,
                source_id=self.source_id,
                publication_time_unavailable=pub_unavailable
            )
            normalized.append(article)
        return normalized

    def get_rate_status(self) -> Dict[str, Any]:
        return {
            "requests_used": self.source_config.get("requests_used", 0),
            "requests_remaining": 999999,
            "window_seconds": 86400
        }
