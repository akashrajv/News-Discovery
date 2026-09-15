from datetime import datetime
from app.schemas.article import ArticleCreate
from app.services.deduplication_service import DeduplicationService
from app.utils.text_utils import normalize_url, normalize_title, compute_content_hash

def test_deduplication_stages():
    now = datetime.utcnow()

    a1 = ArticleCreate(
        title="Tata Motors announces new EV",
        description="Tata Motors unveils new electric car platform.",
        source="Source A",
        url="https://example.com/art1?utm_source=twitter",
        canonical_url=normalize_url("https://example.com/art1?utm_source=twitter"),
        normalized_title=normalize_title("Tata Motors announces new EV"),
        content_hash=compute_content_hash("Tata Motors announces new EV", "Tata Motors unveils new electric car platform.")
    )

    # Exact duplicate URL & Title
    a2 = ArticleCreate(
        title="Tata Motors announces new EV",
        description="Tata Motors unveils new electric car platform.",
        source="Source B",
        url="https://example.com/art1?ref=facebook",
        canonical_url=normalize_url("https://example.com/art1?ref=facebook"),
        normalized_title=normalize_title("Tata Motors announces new EV"),
        content_hash=compute_content_hash("Tata Motors announces new EV", "Tata Motors unveils new electric car platform.")
    )

    # Similar title duplicate
    a3 = ArticleCreate(
        title="Tata Motors announces brand new EV",
        description="Tata Motors unveils brand new electric car platform.",
        source="Source C",
        url="https://example2.com/art3",
        canonical_url=normalize_url("https://example2.com/art3"),
        normalized_title=normalize_title("Tata Motors announces brand new EV"),
        content_hash=compute_content_hash("Tata Motors announces brand new EV", "Tata Motors unveils brand new electric car platform.")
    )

    # Completely different unique article
    a4 = ArticleCreate(
        title="Quarterly profits surge for automotive sector",
        description="Auto manufacturers report strong Q3 earnings.",
        source="Source D",
        url="https://example3.com/art4",
        canonical_url=normalize_url("https://example3.com/art4"),
        normalized_title=normalize_title("Quarterly profits surge for automotive sector"),
        content_hash=compute_content_hash("Quarterly profits surge for automotive sector", "Auto manufacturers report strong Q3 earnings.")
    )

    articles = [a1, a2, a3, a4]
    uniques, dups = DeduplicationService.deduplicate(articles, similarity_threshold=0.8)

    assert len(uniques) == 2
    assert len(dups) == 2
    assert uniques[0].title == "Tata Motors announces new EV"
    assert uniques[1].title == "Quarterly profits surge for automotive sector"
