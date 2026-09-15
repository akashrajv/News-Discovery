import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database.database import SessionLocal
from app.database.models import ArticleModel, SourceModel, CollectionLogModel
from app.registry.source_registry import SourceRegistry
from app.services.rate_limit_service import RateLimitService
from app.services.cost_service import CostService
from app.services.relevance_service import RelevanceService
from app.utils.text_utils import normalize_url, normalize_title, compute_content_hash, compute_dedup_hash
from app.utils.logger import get_logger

logger = get_logger("news_engine.scheduler_service")

class NewsSchedulerService:
    """Service orchestrating background periodic fetch jobs, deduplication upserts, and retention cleanup."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    def start(self):
        """Initialize and start the background scheduler."""
        if not settings.ENABLE_SCHEDULED_FETCHER:
            logger.info("Scheduled fetcher is disabled in settings.")
            return

        fetch_interval = max(1, settings.FETCH_INTERVAL_MINUTES)
        logger.info(f"Starting NewsSchedulerService (Interval: {fetch_interval}m, Retention: {settings.RETENTION_PERIOD_DAYS}d)...")

        # Schedule periodic fetch job
        self.scheduler.add_job(
            self.execute_scheduled_fetch,
            'interval',
            minutes=fetch_interval,
            id='scheduled_news_fetch',
            replace_existing=True
        )

        # Schedule daily retention cleanup job
        self.scheduler.add_job(
            self.execute_retention_cleanup,
            'interval',
            hours=24,
            id='retention_cleanup',
            replace_existing=True
        )

        self.scheduler.start()
        self.is_running = True
        logger.info("Background NewsSchedulerService started successfully.")

    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        if self.is_running:
            logger.info("Shutting down NewsSchedulerService...")
            self.scheduler.shutdown(wait=False)
            self.is_running = False

    async def execute_scheduled_fetch(self):
        """Periodic background job pulling news from all configured sources and upserting into database."""
        logger.info("=== Starting Scheduled Background News Fetch Cycle ===")
        db: Session = SessionLocal()

        total_fetched = 0
        total_inserted = 0
        total_duplicates = 0
        sources_failed = 0

        # Targeted query keywords for automatic background discovery
        default_entities = ["Tata Motors", "NVIDIA", "Tesla", "Apple", "Microsoft"]

        try:
            sources = SourceRegistry.get_all_sources(db)
            enabled_sources = [s for s in sources if s.enabled]

            for source_model in enabled_sources:
                connector = SourceRegistry.get_connector(source_model)
                avail, avail_msg = connector.is_available()

                if not avail:
                    logger.info(f"Skipping source '{source_model.name}' during scheduled fetch: {avail_msg}")
                    continue

                # Rate limit check
                is_allowed, rate_msg, _ = RateLimitService.check_rate_limit(db, source_model.id)
                if not is_allowed:
                    logger.warning(f"Source '{source_model.name}' rate limited: {rate_msg}")
                    sources_failed += 1
                    continue

                # Build query string
                query_str = connector.build_query(
                    entity=" ".join(default_entities[:2]),
                    keywords=["news", "EV", "AI", "tech"]
                )

                start_time = datetime.utcnow()
                try:
                    raw_items = await RateLimitService.execute_with_retry(
                        connector.fetch, query_str, time_window_minutes=1440
                    )
                    normalized_articles = connector.normalize(raw_items)
                    
                    fetched_count = len(normalized_articles)
                    total_fetched += fetched_count

                    # Upsert normalized articles into database
                    inserted, duplicates = self._upsert_articles(db, normalized_articles)
                    total_inserted += inserted
                    total_duplicates += duplicates

                    # Record success & cost metrics
                    RateLimitService.record_request_used(db, source_model.id, success=True)
                    if source_model.connection_method == "api":
                        cost = source_model.estimated_cost_per_request
                        CostService.record_api_usage(db, source_model.id, source_model.name, 1, cost)

                    log_entry = CollectionLogModel(
                        request_id=f"sched_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        source_id=source_model.id,
                        source_name=source_model.name,
                        connector=source_model.connection_method,
                        status="success",
                        articles_fetched=fetched_count,
                        articles_accepted=inserted,
                        duplicates_found=duplicates,
                        duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                    )
                    db.add(log_entry)
                    db.commit()

                    logger.info(
                        f"Source '{source_model.name}': {fetched_count} fetched | {inserted} new inserted | {duplicates} duplicates skipped."
                    )

                except Exception as source_err:
                    db.rollback()
                    logger.error(f"Error fetching from source '{source_model.name}': {source_err}")
                    sources_failed += 1
                    RateLimitService.record_request_used(db, source_model.id, success=False, error_msg=str(source_err))

            logger.info(
                f"=== Scheduled Fetch Cycle Complete: {total_fetched} total fetched | {total_inserted} new inserted | {total_duplicates} duplicates skipped | {sources_failed} sources failed ==="
            )

        except Exception as cycle_err:
            logger.error(f"Scheduled fetch cycle error: {cycle_err}")
        finally:
            db.close()

    def _upsert_articles(self, db: Session, articles) -> tuple[int, int]:
        """
        Upsert logic: Insert if new by URL or dedup_hash; skip if already present in database.
        Returns (inserted_count, duplicate_count).
        """
        inserted = 0
        duplicates = 0

        for art in articles:
            url_val = art.url or art.canonical_url
            if not url_val:
                continue

            dedup_val = art.dedup_hash or compute_dedup_hash(art.title, art.published_at)

            # Check existing article by URL or dedup_hash
            existing = db.query(ArticleModel).filter(
                (ArticleModel.url == url_val) | (ArticleModel.dedup_hash == dedup_val)
            ).first()

            if existing:
                duplicates += 1
                # Update last_seen_at timestamp
                existing.last_seen_at = datetime.utcnow()
                continue

            try:
                # Compute semantic relevance and importance intelligence
                analysis = RelevanceService.compute_semantic_analysis(
                    title=art.title,
                    description=art.description,
                    content=art.content,
                    target_entity=getattr(art, "target_entity", "All Companies") or "All Companies"
                )

                db_article = ArticleModel(
                    title=art.title,
                    description=art.description,
                    content=art.content,
                    source=art.source,
                    published_at=art.published_at or datetime.utcnow(),
                    url=url_val,
                    category=art.category or "General",
                    location=art.location or "Global",
                    collection_method=art.collection_method,
                    collected_at=art.collected_at or datetime.utcnow(),
                    image_url=getattr(art, 'image_url', None),
                    dedup_hash=dedup_val,
                    canonical_url=art.canonical_url or url_val,
                    normalized_title=art.normalized_title or normalize_title(art.title),
                    content_hash=art.content_hash or compute_content_hash(art.title, art.description),
                    source_id=art.source_id,
                    publication_time_unavailable=art.publication_time_unavailable,
                    target_entity=analysis["target_entity"],
                    relevance_score=analysis["relevance_score"],
                    importance_score=analysis["importance_score"],
                    importance_rating=analysis["importance_rating"],
                    sentiment_tone=analysis["sentiment_tone"],
                    ai_summary=analysis["ai_summary"]
                )
                db.add(db_article)
                db.flush()
                inserted += 1
            except IntegrityError:
                db.rollback()
                duplicates += 1
            except Exception as e:
                db.rollback()
                logger.error(f"Error inserting article '{art.title}': {e}")

        db.commit()
        return inserted, duplicates

    def execute_retention_cleanup(self):
        """Purge articles older than RETENTION_PERIOD_DAYS from database."""
        retention_days = max(1, settings.RETENTION_PERIOD_DAYS)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        logger.info(f"Running retention cleanup (Purging articles collected/published prior to {cutoff_date.isoformat()})...")

        db: Session = SessionLocal()
        try:
            deleted_count = db.query(ArticleModel).filter(
                (ArticleModel.collected_at < cutoff_date) & (ArticleModel.published_at < cutoff_date)
            ).delete(synchronize_session=False)

            db.commit()
            logger.info(f"Retention cleanup complete: {deleted_count} expired articles deleted.")
        except Exception as e:
            db.rollback()
            logger.error(f"Retention cleanup error: {e}")
        finally:
            db.close()

# Global scheduler service instance
scheduler_service = NewsSchedulerService()
