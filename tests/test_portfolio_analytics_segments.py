"""Portfolio analytics must differ by overview segment filter."""

from __future__ import annotations

import sqlite3

import pytest

from customer360.api.portfolio_analytics import fetch_portfolio_analytics
from customer360.api.value_history import fetch_value_history
from customer360.paths import default_db_path


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(default_db_path())
    c.row_factory = sqlite3.Row
    yield c
    c.close()


def test_value_history_differs_for_foreclosures(conn: sqlite3.Connection) -> None:
    all_pts = fetch_value_history(conn, segment="customers_all")
    fc_pts = fetch_value_history(conn, segment="with_foreclosures")
    assert len(all_pts) > 0 and len(fc_pts) > 0
    assert all_pts[-1]["total_value"] != fc_pts[-1]["total_value"]


def test_kpis_differs_for_foreclosures(conn: sqlite3.Connection) -> None:
    all_data = fetch_portfolio_analytics(conn, segment="customers_all")
    fc_data = fetch_portfolio_analytics(conn, segment="with_foreclosures")
    assert all_data["kpis"]["active_customers"] > fc_data["kpis"]["active_customers"]
    assert all_data["kpis"]["total_book_value"] > fc_data["kpis"]["total_book_value"]


def test_payload_segment_field(conn: sqlite3.Connection) -> None:
    fc = fetch_portfolio_analytics(conn, segment="with_foreclosures")
    assert fc["segment"] == "with_foreclosures"
