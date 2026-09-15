from datetime import datetime, timedelta
import pytest
from app.database.models import SourceModel
from app.services.rate_limit_service import RateLimitService

def test_pure_helper_get_next_reset_utc():
    """Verify get_next_reset_utc returns next 00:00:00 UTC boundary."""
    dt1 = datetime(2026, 9, 14, 15, 30, 45)
    next_utc1 = RateLimitService.get_next_reset_utc(dt1)
    assert next_utc1 == datetime(2026, 9, 15, 0, 0, 0)

    dt2 = datetime(2026, 9, 14, 0, 0, 0)
    next_utc2 = RateLimitService.get_next_reset_utc(dt2)
    assert next_utc2 == datetime(2026, 9, 15, 0, 0, 0)

def test_quota_reset_exact_boundary(db_session):
    """(a) Test reset occurs exactly at UTC midnight boundary."""
    source = SourceModel(
        id="src_test_boundary",
        name="Test Source Boundary",
        source_type="API",
        connection_method="api",
        request_limit=100,
        requests_used_today=100,
        requests_remaining=0,
        last_reset_at=datetime(2026, 9, 14, 0, 0, 0),
        current_status="RATE_LIMITED"
    )
    db_session.add(source)
    db_session.commit()

    # Exact boundary check at 2026-09-15 00:00:00 UTC
    now_at_boundary = datetime(2026, 9, 15, 0, 0, 0)
    reset_occurred = RateLimitService.check_and_reset_quota(db_session, source, now_utc=now_at_boundary)

    assert reset_occurred is True
    assert source.requests_used_today == 0
    assert source.requests_remaining == 100
    assert source.current_status == "AVAILABLE"
    assert source.last_reset_at == now_at_boundary

def test_app_offline_through_boundary(db_session):
    """(b) Test app offline through boundary: first request after restart detects missed reset."""
    four_days_ago = datetime(2026, 9, 10, 12, 0, 0)
    source = SourceModel(
        id="src_test_offline",
        name="Test Source Offline",
        source_type="API",
        connection_method="api",
        request_limit=50,
        requests_used_today=45,
        requests_remaining=5,
        last_reset_at=four_days_ago,
        current_status="AVAILABLE"
    )
    db_session.add(source)
    db_session.commit()

    # App restarts 4 days later at 2026-09-14 08:30:00 UTC and performs a rate limit check
    now_after_restart = datetime(2026, 9, 14, 8, 30, 0)
    is_allowed, reason, remaining = RateLimitService.check_rate_limit(
        db_session, "src_test_offline", now_utc=now_after_restart
    )

    assert is_allowed is True
    assert remaining == 50
    assert source.requests_used_today == 0
    assert source.last_reset_at == now_after_restart

def test_multiple_sources_independent_resets(db_session):
    """(c) Test multiple sources with different last-reset / last-used timestamps reset independently."""
    source_a = SourceModel(
        id="src_indep_a",
        name="Source A (Needs Reset)",
        source_type="API",
        connection_method="api",
        request_limit=100,
        requests_used_today=80,
        requests_remaining=20,
        last_reset_at=datetime(2026, 9, 14, 0, 0, 0),
        current_status="AVAILABLE"
    )
    source_b = SourceModel(
        id="src_indep_b",
        name="Source B (Already Reset Today)",
        source_type="API",
        connection_method="api",
        request_limit=200,
        requests_used_today=15,
        requests_remaining=185,
        last_reset_at=datetime(2026, 9, 15, 0, 0, 0),
        current_status="AVAILABLE"
    )
    db_session.add_all([source_a, source_b])
    db_session.commit()

    # Current time is 2026-09-15 01:00:00 UTC
    now = datetime(2026, 9, 15, 1, 0, 0)

    # Check reset for Source A
    res_a = RateLimitService.check_and_reset_quota(db_session, source_a, now_utc=now)
    # Check reset for Source B
    res_b = RateLimitService.check_and_reset_quota(db_session, source_b, now_utc=now)

    # Source A should have reset
    assert res_a is True
    assert source_a.requests_used_today == 0
    assert source_a.requests_remaining == 100

    # Source B should NOT have reset (its last_reset_at is 2026-09-15 so next reset is 2026-09-16)
    assert res_b is False
    assert source_b.requests_used_today == 15
    assert source_b.requests_remaining == 185

def test_idempotent_request_recording(db_session):
    """Verify record_request_used accurately increments daily usage and enforces limit."""
    source = SourceModel(
        id="src_record_test",
        name="Test Recording",
        source_type="API",
        connection_method="api",
        request_limit=2,
        requests_used_today=0,
        requests_remaining=2,
        last_reset_at=datetime(2026, 9, 14, 0, 0, 0),
        current_status="AVAILABLE"
    )
    db_session.add(source)
    db_session.commit()

    now = datetime(2026, 9, 14, 10, 0, 0)

    # Record 1st request
    RateLimitService.record_request_used(db_session, "src_record_test", success=True, now_utc=now)
    assert source.requests_used_today == 1
    assert source.requests_remaining == 1
    assert source.current_status == "AVAILABLE"

    # Record 2nd request
    RateLimitService.record_request_used(db_session, "src_record_test", success=True, now_utc=now)
    assert source.requests_used_today == 2
    assert source.requests_remaining == 0
    assert source.current_status == "RATE_LIMITED"

    # 3rd check should be rejected
    is_allowed, reason, remaining = RateLimitService.check_rate_limit(db_session, "src_record_test", now_utc=now)
    assert is_allowed is False
    assert "quota exhausted" in reason
