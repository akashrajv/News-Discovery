import pytest
from app.connectors.rss_connector import RSSConnector

def test_rss_normalization():
    source_config = {
        "id": "src_rss_test",
        "name": "Test RSS Feed",
        "source_type": "RSS",
        "connection_method": "rss",
        "rss_url": "https://example.com/rss.xml"
    }
    connector = RSSConnector(source_config)

    raw_items = [
        {
            "title": "  Tata Motors launches EV sedan ",
            "link": "https://example.com/article1?utm_source=rss&utm_medium=feed",
            "summary": "Electric sedan launched in Mumbai.",
            "published_parsed": (2026, 9, 10, 12, 0, 0, 3, 253, 0)
        }
    ]

    normalized = connector.normalize(raw_items)
    assert len(normalized) == 1
    art = normalized[0]
    assert art.title == "Tata Motors launches EV sedan"
    assert "utm_source" not in art.canonical_url
    assert art.collection_method == "rss"
    assert art.normalized_title == "tata motors launches ev sedan"
