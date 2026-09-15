from datetime import datetime, timedelta
import pytest
from app.schemas.article import ArticleCreate
from app.services.recency_service import RecencyService

def test_recency_filter_weeks_and_months():
    """Verify RecencyService retains articles within weekly, monthly, and yearly windows."""
    now = datetime.utcnow()

    art_10m = ArticleCreate(title="10 min ago", source="Test", url="http://test.com/1", collection_method="api", published_at=now - timedelta(minutes=10))
    art_5d = ArticleCreate(title="5 days ago", source="Test", url="http://test.com/2", collection_method="api", published_at=now - timedelta(days=5))
    art_2w = ArticleCreate(title="2 weeks ago", source="Test", url="http://test.com/3", collection_method="api", published_at=now - timedelta(days=14))
    art_2m = ArticleCreate(title="2 months ago", source="Test", url="http://test.com/4", collection_method="api", published_at=now - timedelta(days=60))
    art_350d = ArticleCreate(title="350 days ago", source="Test", url="http://test.com/5", collection_method="api", published_at=now - timedelta(days=350))

    articles = [art_10m, art_5d, art_2w, art_2m, art_350d]

    # Test 1 week (10080 minutes)
    retained_1w, filtered_1w = RecencyService.filter_by_recency(articles, time_window_minutes=10080)
    assert len(retained_1w) == 2  # 10 min ago and 5 days ago
    assert filtered_1w == 3

    # Test 1 month (43200 minutes / 30 days)
    retained_1m, filtered_1m = RecencyService.filter_by_recency(articles, time_window_minutes=43200)
    assert len(retained_1m) == 3  # 10 min ago, 5 days ago, and 2 weeks ago
    assert filtered_1m == 2

    # Test 3 months (129600 minutes / 90 days)
    retained_3m, filtered_3m = RecencyService.filter_by_recency(articles, time_window_minutes=129600)
    assert len(retained_3m) == 4  # 10 min, 5 days, 2 weeks, 2 months
    assert filtered_3m == 1

    # Test 1 year (525600 minutes / 365 days)
    retained_1y, filtered_1y = RecencyService.filter_by_recency(articles, time_window_minutes=525600)
    assert len(retained_1y) == 5  # All retained
    assert filtered_1y == 0
