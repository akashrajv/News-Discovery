import os
import time
import urllib.parse
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
    """RSS / Atom feed connector with dynamic query injection for Google News & regional feeds."""

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
        tokens = []
        if entity and entity.strip().lower() not in ["all", "all companies"]:
            tokens.append(entity.strip())
        if keywords:
            clean_kws = [k.strip() for k in keywords if k.strip()]
            if clean_kws:
                tokens.append(" ".join(clean_kws))
        if location and location.strip().lower() not in ["global", "all", "all regions", "all sectors"]:
            tokens.append(location.strip())
        return " | ".join(tokens) if tokens else ""

    async def fetch(self, query: str, time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        valid, msg = self.validate_configuration()
        if not valid:
            logger.warning(f"RSS source {self.source_name} invalid: {msg}")
            return []

        # Detect if this is Google News RSS or a dynamic template feed
        is_google_news = "news.google.com" in self.rss_url or "{query}" in self.rss_url or self.source_id == "src_rss_google_news"

        if is_google_news:
            return await self._fetch_dynamic_google_news(query)

        # Standard static RSS feed (BBC, AutoExpress, etc.)
        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                response = await client.get(self.rss_url, headers={"User-Agent": "NewsCollectionEngine/1.0"})
                response.raise_for_status()
                feed_content = response.text
        except Exception as e:
            logger.error(f"Error downloading RSS feed {self.rss_url}: {e}")
            return []

        parsed = feedparser.parse(feed_content)
        entries = parsed.entries or []

        # Local filtering by query terms if provided
        query_terms = [q.lower().strip() for q in query.replace("|", " ").split() if len(q.strip()) > 1 and q.lower() not in ["all", "companies"]]
        matching_entries = []

        for entry in entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            text = f"{title} {summary}".lower()

            if not query_terms or any(term in text for term in query_terms):
                matching_entries.append(entry)

        return matching_entries

    async def _fetch_dynamic_google_news(self, query: str) -> List[Dict[str, Any]]:
        """Fetch targeted real-time articles using Google News RSS search engine."""
        # Parse query segments (entity, keywords, location)
        segments = [s.strip() for s in query.split("|") if s.strip()]
        entity_segment = segments[0] if len(segments) > 0 else ""
        location_segment = segments[2] if len(segments) > 2 else (segments[1] if len(segments) == 2 and not any(k in segments[1].lower() for k in ["ev", "ai", "tech", "gpu", "revenue"]) else "")
        keywords_segment = segments[1] if len(segments) > 1 and segments[1] != location_segment else ""

        # Extract distinct company entities if comma-separated (e.g. "Vee Technologies, Tata Motors")
        entities_to_query = []
        if entity_segment:
            entities_to_query = [e.strip() for e in entity_segment.split(",") if e.strip() and e.strip().lower() not in ["all", "all companies"]]

        if not entities_to_query:
            # Fallback to general Indian business discovery
            base_q = "India business technology companies"
            if location_segment:
                base_q += f" {location_segment}"
            entities_to_query = [base_q]

        collected_entries = []
        seen_links = set()

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # Query each entity individually (up to 5) to guarantee full coverage
            for ent in entities_to_query[:5]:
                q_parts = [ent]
                if location_segment and location_segment.lower() not in ent.lower():
                    q_parts.append(location_segment)
                if keywords_segment:
                    q_parts.append(keywords_segment)
                
                search_term = " ".join(q_parts)
                encoded_q = urllib.parse.quote(search_term)
                target_url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-IN&gl=IN&ceid=IN:en"

                try:
                    res = await client.get(target_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                    if res.status_code == 200:
                        parsed = feedparser.parse(res.text)
                        for entry in parsed.entries or []:
                            link = entry.get("link") or entry.get("id") or entry.get("title")
                            if link not in seen_links:
                                seen_links.add(link)
                                collected_entries.append(entry)
                except Exception as ex:
                    logger.warning(f"Google News RSS fetch error for '{search_term}': {ex}")

        return collected_entries

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
