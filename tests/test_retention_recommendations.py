"""Retention queue recommendations should vary by customer context."""

from __future__ import annotations

import sqlite3

import pytest

from customer360.api.retention_playbook import fetch_retention_playbook
from customer360.api.retention_recommendations import fetch_retention_recommendations
from customer360.paths import default_db_path


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(default_db_path())
    c.row_factory = sqlite3.Row
    yield c
    c.close()


def test_playbook_queue_has_no_inline_actions(conn: sqlite3.Connection) -> None:
    data = fetch_retention_playbook(conn, limit=5)
    assert data["items"]
    assert all(item["recommended_action"] is None for item in data["items"])


def test_batch_recommendations_differ(conn: sqlite3.Connection) -> None:
    queue = fetch_retention_playbook(conn, limit=8)
    ids = [item["customer_id"] for item in queue["items"]]
    assert len(ids) >= 2
    batch = fetch_retention_recommendations(conn, ids)
    by_id = {row["customer_id"]: row["recommended_action"] for row in batch["recommendations"]}
    assert len(by_id) >= 2
    details = {by_id[cid]["detail"] for cid in by_id}
    assert len(details) >= 2, "expected personalized best-next-touch copy per customer"
