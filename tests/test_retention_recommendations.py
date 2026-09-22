"""Retention queue recommendations API."""

from __future__ import annotations

import sqlite3

from customer360.api.retention_playbook import fetch_retention_playbook

from customer360.paths import default_db_path


def test_playbook_queue_has_no_inline_actions() -> None:
    conn = sqlite3.connect(default_db_path())
    conn.row_factory = sqlite3.Row
    try:
        data = fetch_retention_playbook(conn, limit=5)
        assert data["items"]
        assert all(item["recommended_action"] is None for item in data["items"])
    finally:
        conn.close()
