import pytest
from app.services.relevance_service import RelevanceService

def test_company_knowledge_lookup():
    context_nvda = RelevanceService.get_company_context("NVIDIA")
    assert context_nvda["name"] == "NVIDIA"
    assert "gpu" in context_nvda["core_terms"]

    context_tata = RelevanceService.get_company_context("Tata Motors EV")
    assert context_tata["name"] == "Tata Motors"

    context_custom = RelevanceService.get_company_context("Acme Corp")
    assert context_custom["name"] == "Acme Corp"

def test_semantic_analysis_nvidia_critical():
    title = "NVIDIA Announces Acquisition of Next-Gen AI Chip Maker for $10 Billion"
    desc = "NVIDIA unveils massive expansion into data center GPUs and supercomputers."
    analysis = RelevanceService.compute_semantic_analysis(title=title, description=desc, target_entity="NVIDIA")

    assert analysis["target_entity"] == "NVIDIA"
    assert analysis["relevance_score"] >= 80.0
    assert analysis["importance_rating"] == "CRITICAL"
    assert "IMPACT" in analysis["ai_summary"]

def test_semantic_analysis_multi_entity_query():
    target_query = "Tata Motors, NVIDIA, Tesla, Apple, Microsoft"

    # 1. Tata Motors article
    tata_analysis = RelevanceService.compute_semantic_analysis(
        title="Tata Motors unveils new Nexon EV battery upgrade",
        description="Tata Motors updates EV SUV lineup",
        target_entity=target_query
    )
    assert tata_analysis["target_entity"] == "Tata Motors"
    assert tata_analysis["relevance_score"] >= 60.0

    # 2. Tesla article
    tesla_analysis = RelevanceService.compute_semantic_analysis(
        title="Tesla expands Robotaxi Cybercab fleet deployment",
        description="Full self driving autonomous vehicle testing",
        target_entity=target_query
    )
    assert tesla_analysis["target_entity"] == "Tesla"
    assert tesla_analysis["relevance_score"] >= 60.0

    # 3. Completely unrelated article
    unrelated_analysis = RelevanceService.compute_semantic_analysis(
        title="Local Bakery Wins Annual Cupcake Competition",
        description="Freshly baked pastries win gold medal in local county fair",
        target_entity=target_query
    )
    assert unrelated_analysis["relevance_score"] < 30.0

def test_semantic_analysis_low_relevance():
    title = "Local Bakery Wins Baking Competition"
    desc = "A small bakery in Ohio won first prize for its traditional apple pie."
    analysis = RelevanceService.compute_semantic_analysis(title=title, description=desc, target_entity="Apple")

    # Should have low relevance score for Apple Inc.
    assert analysis["relevance_score"] < 40.0
    assert "Low relevance match" in analysis["ai_summary"]

def test_filter_by_relevance():
    class DummyArticle:
        def __init__(self, title, description):
            self.title = title
            self.description = description

    articles = [
        DummyArticle("Tesla Unveils Cybercab Robotaxi", "Elon Musk announces new autonomous EV"),
        DummyArticle("Weather Forecast: Heavy Rain Expected", "Rainstorm coming to coastal region")
    ]

    filtered = RelevanceService.filter_by_relevance(articles, target_entity="Tesla", min_score=50.0)
    assert len(filtered) == 1
    assert filtered[0].title == "Tesla Unveils Cybercab Robotaxi"
    assert filtered[0].relevance_score >= 50.0
    assert filtered[0].importance_rating in ["HIGH", "CRITICAL"]
