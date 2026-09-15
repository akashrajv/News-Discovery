import pytest
from datetime import datetime, timedelta
from app.utils.text_utils import compute_dedup_hash, normalize_title, normalize_url
from app.schemas.article import ArticleCreate
from app.services.scheduler_service import NewsSchedulerService
from app.database.database import SessionLocal, init_db
from app.database.models import ArticleModel

def test_dedup_hash_computation():
    title1 = "NVIDIA Unveils New Blackwell Ultra AI GPUs!"
    title2 = "nvidia unveils new blackwell ultra ai gpus"
    pub_date = "2026-09-12T10:00:00Z"

    hash1 = compute_dedup_hash(title1, pub_date)
    hash2 = compute_dedup_hash(title2, pub_date)

    assert hash1 == hash2, "Deduplication hashes should match for identical normalized title + date."

def test_upsert_articles_prevents_duplicates():
    init_db()
    db = SessionLocal()
    scheduler = NewsSchedulerService()

    now = datetime.utcnow()
    test_article1 = ArticleCreate(
        title="Test Electric Vehicle Launch 2026",
        description="Tata Motors launches new EV platform.",
        content="Full article body...",
        source="Test Feed",
        published_at=now,
        url="https://example.com/ev-launch-2026",
        collection_method="rss",
        dedup_hash=compute_dedup_hash("Test Electric Vehicle Launch 2026", now)
    )

    test_article2 = ArticleCreate(
        title="Test Electric Vehicle Launch 2026",
        description="Tata Motors launches new EV platform from another feed.",
        content="Full article body...",
        source="Duplicate Feed",
        published_at=now,
        url="https://example2.com/ev-launch-2026-alt",
        collection_method="rss",
        dedup_hash=compute_dedup_hash("Test Electric Vehicle Launch 2026", now)
    )

    # First insert -> Should insert 1 new article
    inserted1, dups1 = scheduler._upsert_articles(db, [test_article1])
    assert inserted1 == 1
    assert dups1 == 0

    # Second insert with same dedup_hash -> Should detect duplicate and skip
    inserted2, dups2 = scheduler._upsert_articles(db, [test_article2])
    assert inserted2 == 0
    assert dups2 == 1

    db.close()
