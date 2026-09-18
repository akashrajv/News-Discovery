import os
import time
from datetime import datetime
import feedparser
import httpx
from typing import Dict, Any, List, Optional, Tuple

from app.connectors.base import BaseConnector
from app.schemas.article import ArticleCreate
from app.utils.text_utils import normalize_url, normalize_title, compute_content_hash
from app.utils.logger import get_logger

logger = get_logger("news_engine.rss_connector")

class RSSConnector(BaseConnector):
    """RSS / Atom feed connector using feedparser and httpx."""

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.rss_url = source_config.get("rss_url")

    def validate_configuration(self) -> Tuple[bool, Optional[str]]:
        if not self.rss_url or not self.rss_url.startswith(("http://", "https://")):
            return False, "Invalid or missing RSS feed URL"
        return True, None

    def is_available(self) -> Tuple[bool, str]:
        valid, msg = self.validate_configuration()
        if not valid:
            return False, msg or "RSS configuration invalid"
        if not self.source_config.get("enabled", True):
            return False, "Source is disabled"
        return True, "Available (Public RSS)"

    def build_query(self, entity: str, keywords: List[str], location: Optional[str] = None, category: Optional[str] = None) -> str:
        tokens = [entity] + keywords
        return " ".join([t for t in tokens if t])

    async def fetch(self, query: str, time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        valid, msg = self.validate_configuration()
        if not valid:
            logger.warning(f"RSS source {self.source_name} invalid: {msg}")
            return []

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(self.rss_url, headers={"User-Agent": "NewsCollectionEngine/1.0"})
                response.raise_for_status()
                feed_content = response.text
        except Exception as e:
            logger.error(f"Error downloading RSS feed {self.rss_url}: {e}")
            return []

        parsed = feedparser.parse(feed_content)
        entries = parsed.entries or []

        # Local filtering by query terms if provided
        query_terms = [q.lower() for q in query.split() if len(q) > 1 and q.lower() not in ["all", "companies"]]
        matching_entries = []

        for entry in entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            text = f"{title} {summary}".lower()

            if not query_terms or any(term in text for term in query_terms):
                matching_entries.append(entry)

        return matching_entries

    def normalize(self, raw_items: List[Dict[str, Any]]) -> List[ArticleCreate]:
        normalized = []
        for entry in raw_items:
            title = entry.get("title", "").strip()
            if not title:
                continue

            link = entry.get("link", "").strip()
            summary = entry.get("summary", "") or entry.get("description", "")
            
            # Parse publication timestamp
            published_dt = None
            pub_unavailable = False
            published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
            if published_parsed:
                try:
                    published_dt = datetime.fromtimestamp(time.mktime(published_parsed))
                except Exception:
                    pub_unavailable = True
            else:
                pub_unavailable = True

            author = entry.get("author") or entry.get("dc:creator") or (entry.get("author_detail") or {}).get("name")
            if author:
                author = author.strip()

            norm_url = normalize_url(link)
            norm_t = normalize_title(title)
            c_hash = compute_content_hash(title, summary)

            article = ArticleCreate(
                title=title,
                description=summary if summary else None,
                content=None,  # Do not assume full article content in RSS
                source=self.source_name,
                author=author or None,
                published_at=published_dt,
                url=link or f"https://rss.feed/{c_hash}",
                category=self.source_config.get("category"),
                location=self.source_config.get("location"),
                collection_method="rss",
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
            "window_seconds": self.source_config.get("rate_limit_window_seconds", 86400)
        }
