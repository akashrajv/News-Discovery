from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx

from app.connectors.api_connector import BaseAPIConnector
from app.schemas.article import ArticleCreate
from app.utils.text_utils import normalize_url, normalize_title, compute_content_hash
from app.utils.logger import get_logger

logger = get_logger("news_engine.newsdata")

class NewsDataConnector(BaseAPIConnector):
    """Adapter for NewsData.io API (https://newsdata.io)."""

    def build_query(self, entity: str, keywords: List[str], location: Optional[str] = None, category: Optional[str] = None) -> str:
        clean_entity = entity.split(",")[0].strip() if "," in entity else entity.strip()
        tokens = [clean_entity] + [k for k in keywords if k]
        return " ".join(tokens)

    async def fetch(self, query: str, time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        avail, msg = self.is_available()
        if not avail:
            logger.info(f"NewsData.io unavailable: {msg}")
            return []

        endpoint = self.api_endpoint or "https://newsdata.io/api/1/news"
        params = {
            "q": query,
            "apikey": self.api_key,
            "language": "en"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(endpoint, params=params)
                resp.raise_for_status()
                data = resp.json()
                return data.get("results", [])
        except Exception as e:
            logger.error(f"NewsData.io fetch error: {e}")
            return []

    def normalize(self, raw_items: List[Dict[str, Any]]) -> List[ArticleCreate]:
        normalized = []
        for item in raw_items:
            title = (item.get("title") or "").strip()
            if not title:
                continue

            url = (item.get("link") or "").strip()
            description = item.get("description")
            raw_content = item.get("content")
            content = description if (raw_content == "ONLY AVAILABLE IN PAID PLANS" or not raw_content) else raw_content
            source_name = item.get("source_name") or item.get("source_id") or self.source_name
            published_str = item.get("pubDate")

            published_dt = None
            pub_unavailable = False
            if published_str:
                try:
                    published_dt = datetime.fromisoformat(published_str.replace(" ", "T"))
                except Exception:
                    pub_unavailable = True
            else:
                pub_unavailable = True

            norm_url = normalize_url(url)
            norm_t = normalize_title(title)
            c_hash = compute_content_hash(title, description)

            article = ArticleCreate(
                title=title,
                description=description,
                content=content,
                source=source_name,
                published_at=published_dt,
                url=url or f"https://newsdata.io/article/{c_hash}",
                category=self.source_config.get("category"),
                location=self.source_config.get("location"),
                collection_method="api",
                canonical_url=norm_url,
                normalized_title=norm_t,
                content_hash=c_hash,
                source_id=self.source_id,
                publication_time_unavailable=pub_unavailable
            )
            normalized.append(article)
        return normalized
