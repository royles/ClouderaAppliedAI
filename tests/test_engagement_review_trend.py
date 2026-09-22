"""Engagement objective trend includes monthly average review scores."""

from __future__ import annotations

import sqlite3

import pytest

from customer360.api.portfolio_objectives import fetch_engagement_trend
from customer360.interactions.summary import interactions_table_exists
from customer360.paths import default_db_path


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(default_db_path())
    c.row_factory = sqlite3.Row
    yield c
    c.close()


def test_engagement_trend_includes_avg_review_rating(conn: sqlite3.Connection) -> None:
    if not interactions_table_exists(conn):
        pytest.skip("interaction events table not present")
    trend = fetch_engagement_trend(conn, segment="customers_all")
    assert isinstance(trend, list)
    if not trend:
        pytest.skip("no engagement trend rows in seed data")
    assert "avg_review_rating" in trend[0]
    rated = [p for p in trend if p["review_events"] > 0]
    if rated:
        assert any(p["avg_review_rating"] is not None for p in rated)
        for p in rated:
            if p["avg_review_rating"] is not None:
                assert 1.0 <= p["avg_review_rating"] <= 5.0
