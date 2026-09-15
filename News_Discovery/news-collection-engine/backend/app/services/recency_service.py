from datetime import datetime, timedelta, timezone
from typing import List, Tuple
from app.schemas.article import ArticleCreate
from app.utils.logger import get_logger

logger = get_logger("news_engine.recency_service")

class RecencyService:
    """Filters articles based on publication timestamp recency windows (10m, 30m, 1h, 6h, 24h)."""

    @staticmethod
    def filter_by_recency(
        articles: List[ArticleCreate],
        time_window_minutes: int = 60
    ) -> Tuple[List[ArticleCreate], int]:
        """
        Filter articles by published_at within cutoff window.
        Returns (retained_articles, filtered_out_count).
        """
        now_utc = datetime.utcnow()
        cutoff_dt = now_utc - timedelta(minutes=time_window_minutes)

        retained = []
        filtered_count = 0

        for article in articles:
            if article.published_at is None or article.publication_time_unavailable:
                # Keep article when publication timestamp is unknown, but flag it
                article.publication_time_unavailable = True
                retained.append(article)
                continue

            # Naive or UTC timezone normalization
            pub_dt = article.published_at
            if pub_dt.tzinfo is not None:
                pub_dt = pub_dt.astimezone(timezone.utc).replace(tzinfo=None)

            if pub_dt >= cutoff_dt:
                retained.append(article)
            else:
                filtered_count += 1

        logger.info(f"Recency filter ({time_window_minutes}m window): Retained {len(retained)}, Filtered {filtered_count}")
        return retained, filtered_count
