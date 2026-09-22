"""Retention queue LLM JSON parsing and length limits."""

from __future__ import annotations

import pytest

from customer360.api.retention_queue_llm import (
    MAX_DETAIL_LEN,
    MAX_TITLE_LEN,
    _clamp,
    _parse_batch_json,
)


def test_parse_batch_json_and_clamp_lengths() -> None:
    raw = """
    {
      "items": [
        {
          "customer_id": 101,
          "title": "Call Ron in Netanya about open billing question on pension policy",
          "detail": "Phone today — he searched help center twice this month and has an unresolved agent ticket about premium timing."
        },
        {
          "customer_id": 202,
          "title": "Email Dana a policy summary",
          "detail": "Send a concise email covering her two active health policies after 94 days without login."
        }
      ]
    }
    """
    rows = _parse_batch_json(raw, {101, 202})
    assert len(rows) == 2
    for row in rows:
        action = row["recommended_action"]
        assert len(action["title"]) <= MAX_TITLE_LEN
        assert len(action["detail"]) <= MAX_DETAIL_LEN
    assert rows[0]["customer_id"] == 101


def test_clamp_adds_ellipsis() -> None:
    long = "x" * 80
    assert len(_clamp(long, 20)) == 20
    assert _clamp(long, 20).endswith("…")
