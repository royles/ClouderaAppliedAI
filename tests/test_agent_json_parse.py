import json

from customer360.agent.bedrock_agent import _parse_agent_json
from customer360.agent.json_parse import load_first_json_object


def test_load_json_with_trailing_prose():
    inner = {
        "answer": "Book value is stable.",
        "action_ids": ["business"],
        "open_retention_playbook": False,
    }
    raw = json.dumps(inner) + "\n\nLet me know if you need more."
    data = load_first_json_object(raw)
    assert data["answer"] == inner["answer"]


def test_load_json_in_fences():
    raw = (
        '```json\n{"answer": "Hi", "action_ids": [], '
        '"open_retention_playbook": false}\n```'
    )
    data = load_first_json_object(raw)
    assert data["answer"] == "Hi"


def test_parse_agent_json_requires_answer():
    raw = json.dumps(
        {
            "answer": "  Portfolio KPIs look healthy.  ",
            "action_ids": ["business"],
            "open_retention_playbook": False,
        }
    )
    parsed = _parse_agent_json(raw)
    assert "healthy" in parsed["answer"]
