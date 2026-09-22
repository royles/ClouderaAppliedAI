"""Retention queue recommendations API."""

from __future__ import annotations

import sqlite3

import pytest

from customer360.api.retention_playbook import fetch_retention_playbook
from customer360.api.retention_recommendations import fetch_retention_recommendations
from customer360.llm.router import is_llm_configured
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


def test_batch_recommendations_use_llm_when_configured(conn: sqlite3.Connection) -> None:
    queue = fetch_retention_playbook(conn, limit=6)
    ids = [item["customer_id"] for item in queue["items"]]
    assert len(ids) >= 2
    batch = fetch_retention_recommendations(conn, ids, locale="en")
    assert "llm_configured" in batch
    if not is_llm_configured():
        assert batch["llm_configured"] is False
        assert batch["recommendations"] == []
        return
    assert batch["llm_configured"] is True
    assert len(batch["recommendations"]) >= 2
    details = {row["recommended_action"]["detail"] for row in batch["recommendations"]}
    assert len(details) >= 2
