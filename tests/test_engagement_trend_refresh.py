"""Stale objective caches must still expose monthly review averages."""

from __future__ import annotations

from customer360.api.portfolio_objectives import (
    engagement_trend_needs_avg_refresh,
    ensure_engagement_review_averages,
)


def test_engagement_trend_needs_avg_refresh_when_reviews_without_avg() -> None:
    stale = [{"period": "2025-01-01", "review_events": 3, "avg_review_rating": None}]
    assert engagement_trend_needs_avg_refresh(stale) is True


def test_engagement_trend_needs_avg_refresh_when_avg_present() -> None:
    ok = [{"period": "2025-01-01", "review_events": 3, "avg_review_rating": 4.2}]
    assert engagement_trend_needs_avg_refresh(ok) is False


def test_ensure_engagement_keeps_fresh_trends() -> None:
    ok = [{"period": "2025-01-01", "review_events": 1, "avg_review_rating": 5.0}]
    assert ensure_engagement_review_averages(None, ok, segment="customers_all") == ok
