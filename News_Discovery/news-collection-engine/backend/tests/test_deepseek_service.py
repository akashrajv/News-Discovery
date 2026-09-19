import pytest
from app.services.deepseek_service import DeepSeekService

def test_deepseek_service_status():
    service = DeepSeekService()
    status = service.get_status()
    assert "status" in status
    assert status["model"] == "deepseek-reasoner"
    assert "base_url" in status

def test_deepseek_reasoning_trace_generation():
    service = DeepSeekService()

    # Test high-relevance article for NVIDIA
    title = "NVIDIA Reports Record Q3 Revenue Driven by Blackwell Data Center Demand"
    desc = "Jensen Huang announces exponential growth in AI enterprise supercomputing infrastructure."
    analysis = service.analyze_article(
        title=title,
        description=desc,
        target_entity="NVIDIA",
        keywords=["AI", "GPU", "revenue"]
    )

    assert analysis["target_entity"] == "NVIDIA"
    assert analysis["relevance_score"] >= 65.0
    assert analysis["importance_rating"] in ["HIGH", "CRITICAL"]
    assert "reasoning_trace" in analysis
    assert len(analysis["reasoning_trace"]) > 50
    assert "Target Entity Identification" in analysis["reasoning_trace"]
    assert "Relevance Conclusion" in analysis["reasoning_trace"]

def test_deepseek_low_relevance_reasoning():
    service = DeepSeekService()

    title = "Local High School Football Team Wins State Championship"
    desc = "Celebrations erupted in town after the dramatic overtime victory."
    analysis = service.analyze_article(
        title=title,
        description=desc,
        target_entity="Tesla",
        keywords=["EV"]
    )

    assert analysis["relevance_score"] <= 20.0
    assert "reasoning_trace" in analysis
    assert "No Direct Entity Match" in analysis["reasoning_trace"]

def test_deepseek_json_extractor():
    service = DeepSeekService()
    sample_text = 'Here is the analysis:\n```json\n{"target_entity": "Apple", "relevance_score": 85.0, "importance_rating": "HIGH"}\n```'
    extracted = service._extract_json(sample_text)
    assert extracted is not None
    assert extracted["target_entity"] == "Apple"
    assert extracted["relevance_score"] == 85.0
