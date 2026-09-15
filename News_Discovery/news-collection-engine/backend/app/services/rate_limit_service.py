import os
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.database.models import SourceModel
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("news_engine.rate_limit_service")

class RateLimitService:
    """Manages source-level rate limit counters, UTC quota resets, and exponential backoff retry execution."""

    @staticmethod
    def get_next_reset_utc(last_reset_at: Optional[datetime]) -> datetime:
        """Returns the next midnight (00:00:00) UTC boundary after last_reset_at."""
        if not last_reset_at:
            now = datetime.utcnow()
            reset_base = datetime(now.year, now.month, now.day)
        else:
            reset_base = datetime(last_reset_at.year, last_reset_at.month, last_reset_at.day)
        return reset_base + timedelta(days=1)

    @staticmethod
    def check_and_reset_quota(db: Session, source: SourceModel, now_utc: Optional[datetime] = None) -> bool:
        """
        Idempotently checks if the current UTC time has passed the source's next reset boundary.
        If true, resets requests_used_today to 0, resets remaining quota, updates last_reset_at, and persists to DB.
        Returns True if a reset occurred, False otherwise.
        """
        if not source:
            return False

        if now_utc is None:
            now_utc = datetime.utcnow()

        if source.last_reset_at is None:
            source.last_reset_at = datetime(now_utc.year, now_utc.month, now_utc.day)
            source.requests_used_today = source.requests_used_today or 0
            db.commit()

        next_reset = RateLimitService.get_next_reset_utc(source.last_reset_at)

        if now_utc >= next_reset:
            source.requests_used_today = 0
            source.requests_used = 0
            source.requests_remaining = source.request_limit or 100
            source.last_reset_at = now_utc
            if source.current_status == "RATE_LIMITED":
                env_key = source.api_key_env_name
                key_configured = bool(os.getenv(env_key)) if env_key else True
                if source.connection_method == "rss" or key_configured:
                    source.current_status = "AVAILABLE"
            db.commit()
            logger.info(f"Quota reset triggered for source {source.id} at {now_utc.isoformat()} UTC.")
            return True

        return False

    @staticmethod
    def check_rate_limit(db: Session, source_id: str, now_utc: Optional[datetime] = None) -> Tuple[bool, str, int]:
        """
        Check if source is within rate limit window.
        Returns (is_allowed, status_code_or_reason, remaining_quota).
        """
        source = db.query(SourceModel).filter(SourceModel.id == source_id).first()
        if not source:
            return False, "source_not_found", 0

        current_now = now_utc or datetime.utcnow()
        RateLimitService.check_and_reset_quota(db, source, now_utc=current_now)

        # Check if source is currently in retry delay after failure
        if source.retry_after and current_now < source.retry_after:
            wait_seconds = int((source.retry_after - current_now).total_seconds())
            return False, f"RATE_LIMITED (retry after {wait_seconds}s)", source.requests_remaining

        if source.requests_remaining <= 0:
            source.current_status = "RATE_LIMITED"
            db.commit()
            return False, "RATE_LIMITED (quota exhausted)", 0

        return True, "ALLOWED", source.requests_remaining

    @staticmethod
    def record_request_used(db: Session, source_id: str, success: bool = True, error_msg: str = None, now_utc: Optional[datetime] = None):
        """Decrement remaining quota and update source timestamps/status."""
        source = db.query(SourceModel).filter(SourceModel.id == source_id).first()
        if not source:
            return

        current_now = now_utc or datetime.utcnow()
        RateLimitService.check_and_reset_quota(db, source, now_utc=current_now)

        source.requests_used_today = (source.requests_used_today or 0) + 1
        source.requests_used = (source.requests_used or 0) + 1
        source.requests_remaining = max(0, (source.request_limit or 100) - source.requests_used_today)
        source.updated_at = current_now

        if source.requests_remaining <= 0:
            source.current_status = "RATE_LIMITED"

        if success:
            source.last_successful_collection = current_now
            source.last_error = None
            source.retry_after = None
            if source.requests_remaining > 0 and source.current_status == "RATE_LIMITED":
                source.current_status = "AVAILABLE"
        else:
            source.last_error = error_msg
            if source.requests_remaining > 0:
                source.current_status = "FAILED"
            source.retry_after = current_now + timedelta(seconds=30)

        db.commit()

    @staticmethod
    async def execute_with_retry(async_func, *args, **kwargs):
        """Execute async function with exponential backoff retry via tenacity."""
        attempts = settings.MAX_RETRY_ATTEMPTS
        multiplier = settings.RETRY_BACKOFF_FACTOR

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(attempts),
                wait=wait_exponential(multiplier=multiplier, min=1, max=10),
                reraise=True
            ):
                with attempt:
                    return await async_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Execution failed after {attempts} retry attempts: {e}")
            raise e
