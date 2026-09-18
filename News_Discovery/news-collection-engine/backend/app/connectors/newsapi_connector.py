from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx

from app.connectors.api_connector import BaseAPIConnector
from app.schemas.article import ArticleCreate
from app.utils.text_utils import normalize_url, normalize_title, compute_content_hash
from app.utils.logger import get_logger

logger = get_logger("news_engine.newsapi")

class NewsAPIConnector(BaseAPIConnector):
    """Adapter for NewsAPI (https://newsapi.org)."""

    def build_query(self, entity: str, keywords: List[str], location: Optional[str] = None, category: Optional[str] = None) -> str:
        tokens = [f'"{entity}"'] if " " in entity else [entity]
        tokens.extend(keywords)
        return " AND ".join(tokens) if len(tokens) > 1 else entity

    async def fetch(self, query: str, time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        avail, msg = self.is_available()
        if not avail:
            logger.info(f"NewsAPI unavailable: {msg}")
            return []

        endpoint = self.api_endpoint or "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": self.api_key,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 20
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(endpoint, params=params)
                resp.raise_for_status()
                data = resp.json()
                return data.get("articles", [])
        except Exception as e:
            logger.error(f"NewsAPI fetch error: {e}")
            return []

    def normalize(self, raw_items: List[Dict[str, Any]]) -> List[ArticleCreate]:
        normalized = []
        for item in raw_items:
            title = (item.get("title") or "").strip()
            if not title or title == "[Removed]":
                continue

            url = (item.get("url") or "").strip()
            description = item.get("description")
            content = item.get("content")
            source_name = item.get("source", {}).get("name") or self.source_name
            published_str = item.get("publishedAt")

            published_dt = None
            pub_unavailable = False
            if published_str:
                try:
                    published_dt = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                except Exception:
                    pub_unavailable = True
            else:
                pub_unavailable = True

            author = (item.get("author") or "").strip() or None

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
                url=url or f"https://newsapi.org/article/{c_hash}",
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
