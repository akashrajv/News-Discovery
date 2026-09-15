from app.router.source_router import SourceRouter

def test_source_router_evaluation(db_session):
    router = SourceRouter(db_session)
    
    # Test router in live mode (demo_mode=False)
    decision = router.evaluate_routing("req_test_1", entity="Tata Motors", cache_hit=False, demo_mode=False)
    
    assert decision.cache_decision == "MISS"
    assert len(decision.selected_sources) > 0
    # RSS feed should be selected because public RSS has priority and zero cost
    rss_selected = any(s.connection_method == "rss" for s in decision.selected_sources)
    assert rss_selected is True

def test_source_router_cache_hit(db_session):
    router = SourceRouter(db_session)
    decision = router.evaluate_routing("req_test_2", entity="Tata Motors", cache_hit=True, demo_mode=False)
    
    assert decision.cache_decision == "HIT"
    assert len(decision.selected_sources) == 0
    assert len(decision.skipped_sources) > 0
