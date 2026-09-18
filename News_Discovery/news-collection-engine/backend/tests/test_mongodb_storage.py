import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.database.mongodb import MongoDBManager, sanitize_mongodb_uri
from app.schemas.article import ArticleRead


def test_sanitize_mongodb_uri():
    # Test 1: Password with < >
    raw = "mongodb+srv://user:<myPass123>@cluster0.mongodb.net/test?retryWrites=true"
    sanitized = sanitize_mongodb_uri(raw)
    assert "<" not in sanitized and ">" not in sanitized
    assert "user:myPass123@" in sanitized

    # Test 2: Password with @ character unescaped
    raw_with_at = "mongodb+srv://user:Akash@1106@cluster0.mongodb.net/news?retryWrites=true"
    sanitized_at = sanitize_mongodb_uri(raw_with_at)
    assert "user:Akash%401106@" in sanitized_at

    # Test 3: Already encoded password remains encoded properly
    raw_encoded = "mongodb+srv://user:Akash%401106@cluster0.mongodb.net/news?retryWrites=true"
    sanitized_encoded = sanitize_mongodb_uri(raw_encoded)
    assert "user:Akash%401106@" in sanitized_encoded

    # Test 4: Empty / non-matching string
    assert sanitize_mongodb_uri("") == ""
    assert sanitize_mongodb_uri("sqlite:///test.db") == "sqlite:///test.db"


def test_clean_doc_for_return():
    manager = MongoDBManager()

    # Empty doc
    assert manager.clean_doc_for_return({}) == {}

    # Doc with _id and string timestamps
    doc = {
        "_id": "507f1f77bcf86cd799439011",
        "title": "Test Title",
        "url": "https://example.com/test",
        "source": "TestSource",
        "published_at": "2026-09-16T12:00:00Z",
        "collected_at": "2026-09-16T12:05:00Z",
    }
    cleaned = manager.clean_doc_for_return(doc)
    assert cleaned["id"] == "507f1f77bcf86cd799439011"
    assert "_id" not in cleaned
    assert isinstance(cleaned["published_at"], datetime)
    assert isinstance(cleaned["first_seen_at"], datetime)
    assert isinstance(cleaned["last_seen_at"], datetime)


def test_mongodb_status_unconfigured():
    manager = MongoDBManager()
    with patch("app.database.mongodb.settings.MONGODB_URL", None):
        status = manager.get_status()
        assert status["configured"] is False
        assert status["status"] == "unconfigured"


def test_mongodb_status_connected():
    manager = MongoDBManager()
    manager.is_connected = True
    manager.db = MagicMock()
    manager.db.articles.count_documents.return_value = 42

    status = manager.get_status()
    assert status["configured"] is True
    assert status["status"] == "connected"
    assert status["articles_count"] == 42


def test_mongodb_upsert_and_query_mocked():
    manager = MongoDBManager()
    manager.is_connected = True
    mock_db = MagicMock()
    manager.db = mock_db

    mock_db.articles.count_documents.return_value = 1
    mock_db.articles.find.return_value.sort.return_value.skip.return_value.limit.return_value = [
        {
            "_id": "60c72b2f9b1d8b2bad000001",
            "id": "mongo_art_1",
            "title": "Mocked News Title",
            "description": "Mocked news description",
            "content": "Full content",
            "source": "MockSource",
            "url": "https://example.com/mock-article",
            "category": "Technology",
            "target_entity": "Tata Motors",
            "relevance_score": 92.5,
            "importance_score": 85.0,
            "importance_rating": "HIGH",
            "sentiment_tone": "Positive",
            "published_at": datetime.utcnow(),
            "collected_at": datetime.utcnow(),
            "first_seen_at": datetime.utcnow(),
            "last_seen_at": datetime.utcnow(),
        }
    ]

    articles, total = manager.get_articles(entity="Tata Motors", limit=10)
    assert total == 1
    assert len(articles) == 1
    assert articles[0]["title"] == "Mocked News Title"
    assert articles[0]["relevance_score"] == 92.5

    # Validate schema compatibility
    validated = ArticleRead.model_validate(articles[0])
    assert validated.id == "mongo_art_1"
    assert validated.target_entity == "Tata Motors"


def test_mongodb_graceful_fallback_when_offline():
    manager = MongoDBManager()
    manager.is_connected = False
    manager.db = None

    articles, total = manager.get_articles()
    assert articles == []
    assert total == 0

    assert manager.get_article_by_id("123") is None
    assert manager.upsert_article({"url": "https://test.com"}) is False
    assert manager.bulk_upsert_articles([{"url": "https://test.com"}]) == 0
