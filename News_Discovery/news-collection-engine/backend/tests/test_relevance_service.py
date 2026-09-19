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

def test_spurious_match_openai_vs_open_house():
    """Verify that 'Open House' does not spuriously trigger high relevance for 'Open AI'."""
    title = "Burlington Data Centre Open House Draws Questions, Concerns from Residents"
    desc = "Community members gathered at the open house meeting regarding the proposed data center."
    analysis = RelevanceService.compute_semantic_analysis(title=title, description=desc, target_entity="Open AI")

    assert analysis["relevance_score"] < 30.0
    assert "Low relevance" in analysis["ai_summary"]

def test_filter_by_relevance_threshold_tiers():
    class DummyArticle:
        def __init__(self, title, description):
            self.title = title
            self.description = description

    articles = [
        DummyArticle("Apple Launches New M4 MacBook Pro with Generative AI Intelligence", "Apple Inc introduces groundbreaking silicon for MacBook lineup with Apple Intelligence."),
        DummyArticle("Apple Orchard Farms Announces Autumn Harvest Festival", "Local farm opens apple picking season for families in the upstate orchard."),
        DummyArticle("Tech Industry Trends Overview", "General quarterly review mentioning Apple, Google and Microsoft market performance."),
    ]

    # At 60% threshold, only direct Apple hardware/AI news should qualify
    retained_60 = RelevanceService.filter_by_relevance(articles, target_entity="Apple", min_score=60.0)
    assert len(retained_60) == 1
    assert "M4 MacBook Pro" in retained_60[0].title

    # At 75% threshold, same high confidence article retained
    retained_75 = RelevanceService.filter_by_relevance(articles, target_entity="Apple", min_score=75.0)
    assert len(retained_75) == 1
    assert retained_75[0].relevance_score >= 75.0

    # At 95% threshold, filters out when bar is extremely high unless peak match
    retained_95 = RelevanceService.filter_by_relevance(articles, target_entity="Apple", min_score=95.0)
    assert len(retained_95) <= 1

def test_semantic_analysis_strict_keyword_matching():
    """Verify that an article must match both the target company and the user-specified keywords."""
    # Case 1: Matches company (Tesla) AND keyword (robotaxi) -> HIGH relevance
    res_match = RelevanceService.compute_semantic_analysis(
        title="Tesla Unveils Cybercab Robotaxi Autonomous Fleet",
        description="Autonomous driving technology showcase in California",
        target_entity="Tesla",
        keywords=["robotaxi", "cybercab"]
    )
    assert res_match["relevance_score"] >= 70.0

    # Case 2: Matches company (Tesla) BUT MISSES user keyword (lithium, mining) -> LOW relevance
    res_miss = RelevanceService.compute_semantic_analysis(
        title="Tesla Unveils Cybercab Robotaxi Autonomous Fleet",
        description="Autonomous driving technology showcase in California",
        target_entity="Tesla",
        keywords=["lithium mining", "raw materials supply chain"]
    )
    assert res_miss["relevance_score"] <= 25.0

