import json

import pytest

from customer360.insights.parse import parse_insight_json


def test_parse_narrative_insight_json():
    payload = {
        "preamble": "Worth a proactive check-in this week.",
        "summary": "Active customer with two policies.",
        "primary_focus": "retention",
        "guidance": "First paragraph on retention.\n\nSecond paragraph with specifics.",
        "suggested_actions": [
            "Send an email summarizing active policies.",
            "Schedule a call to resolve open agent questions.",
        ],
        "experience_note": "Email first, then call if no reply.",
    }
    parsed = parse_insight_json(json.dumps(payload))
    assert parsed["preamble"] == payload["preamble"]
    assert parsed["guidance"].count("\n\n") == 1
    assert len(parsed["recommendations"]) == 2


def test_parse_legacy_recommendations_only():
    payload = {
        "summary": "Summary line.",
        "primary_focus": "upsell",
        "recommendations": ["Send an email with policy health summary."],
        "experience_note": "Email works best.",
    }
    parsed = parse_insight_json(json.dumps(payload))
    assert parsed["guidance"]
    assert parsed["recommendations"][0].startswith("Send")


def test_parse_rejects_empty_summary():
    with pytest.raises(ValueError):
        parse_insight_json(json.dumps({"guidance": "Only guidance."}))
