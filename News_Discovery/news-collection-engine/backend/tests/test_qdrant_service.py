import pytest
from app.services.qdrant_service import QdrantVectorService, SemanticVectorizer

def test_semantic_vectorizer():
    vec = SemanticVectorizer.embed_text("NVIDIA Blackwell GPU supercomputer")
    assert len(vec) == 384
    # Check unit normalization
    import numpy as np
    norm = np.linalg.norm(vec)
    assert pytest.approx(norm, rel=1e-3) == 1.0

def test_qdrant_service_lifecycle():
    # Test service initialization
    service = QdrantVectorService()
    assert service.is_connected is True
    status = service.get_status()
    assert status["status"] == "connected"
    assert status["dimension"] == 384

    # Test single article upsert
    test_article = {
        "id": "art_test_qdrant_1",
        "title": "NVIDIA Unveils Blackwell Ultra AI Superchips",
        "description": "Next-generation GPU architecture designed for generative AI models and data centers.",
        "source": "TechCrunch",
        "url": "https://example.com/nvidia-blackwell",
        "target_entity": "NVIDIA",
        "relevance_score": 95.0,
        "importance_rating": "CRITICAL"
    }

    point_id = service.upsert_article(test_article)
    assert point_id is not None

    # Test bulk upsert
    batch = [
        {
            "id": "art_test_qdrant_2",
            "title": "Tesla Announces Cybercab Robotaxi Production Schedule",
            "description": "Autonomous electric vehicle fleet to begin manufacturing next year.",
            "source": "Electrek",
            "url": "https://example.com/tesla-cybercab",
            "target_entity": "Tesla",
            "relevance_score": 90.0,
            "importance_rating": "HIGH"
        },
        {
            "id": "art_test_qdrant_3",
            "title": "Apple Previews M4 Max Silicon for Pro Devices",
            "description": "Apple Silicon upgrades neural engine performance for on-device AI tasks.",
            "source": "The Verge",
            "url": "https://example.com/apple-m4",
            "target_entity": "Apple",
            "relevance_score": 88.0,
            "importance_rating": "HIGH"
        }
    ]
    count = service.bulk_upsert(batch)
    assert count == 2

    # Test semantic search for AI chips
    results = service.semantic_search(query="AI GPU chip supercomputing", limit=5, min_score=0.2)
    assert len(results) > 0
    top_result = results[0]
    assert "nvidia" in top_result["title"].lower() or "ai" in top_result["title"].lower()
    assert top_result["similarity_score"] > 0.3

    # Test find similar articles
    similar = service.find_similar_articles(article_id="art_test_qdrant_1", limit=2, min_score=0.1)
    # Should find other tech / AI articles in the pool
    assert isinstance(similar, list)
