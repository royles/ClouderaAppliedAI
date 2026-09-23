"""Retention queue LLM JSON parsing and length limits."""

from __future__ import annotations

from customer360.api.retention_queue_llm import (
    MAX_DETAIL_LEN,
    MAX_TITLE_LEN,
    _clamp,
    parse_single_action_json,
)


def test_parse_single_action_json_and_clamp_lengths() -> None:
    raw = """
    {
      "title": "Call Ron in Netanya about open billing question on pension policy",
      "detail": "Phone today — he searched help center twice this month and has an unresolved agent ticket about premium timing."
    }
    """
    row = parse_single_action_json(raw, 101)
    assert row["customer_id"] == 101
    action = row["recommended_action"]
    assert len(action["title"]) <= MAX_TITLE_LEN
    assert len(action["detail"]) <= MAX_DETAIL_LEN


def test_clamp_adds_ellipsis() -> None:
    long = "x" * 80
    assert len(_clamp(long, 20)) == 20
    assert _clamp(long, 20).endswith("…")
