import json

from customer360.actions.bedrock_draft import _parse_draft_json


def test_parse_draft_json_with_trailing_prose():
    inner = {
        "channel": "email",
        "subject": "Your policies",
        "body": "Hello,\n\nWe reviewed your account.\n\nCustomer Care",
    }
    raw = json.dumps(inner) + "\n\nHope this helps."
    parsed = _parse_draft_json(raw)
    assert parsed["channel"] == "email"
    assert parsed["subject"] == "Your policies"


def test_parse_draft_json_in_fences():
    raw = '```json\n{"channel": "sms", "subject": null, "body": "Hi — visit https://portal.example.co.il/m/1"}\n```'
    parsed = _parse_draft_json(raw)
    assert parsed["channel"] == "sms"
    assert parsed["subject"] is None
