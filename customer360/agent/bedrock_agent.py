"""Bedrock-backed executive copilot with JSON validation."""

from __future__ import annotations

import json
import logging
import re

from customer360.agent.actions import actions_from_model_ids
from customer360.agent.prompt import build_system_prompt, build_user_prompt
from customer360.bedrock.client import BedrockError, invoke_text, is_bedrock_configured

logger = logging.getLogger(__name__)


def _parse_agent_json(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        match = re.search(r"\{[\s\S]*\}", stripped)
        if not match:
            raise ValueError("Model did not return JSON") from exc
        data = json.loads(match.group(0))

    answer = str(data.get("answer", "")).strip()
    if not answer:
        raise ValueError("Missing answer in copilot JSON")

    raw_ids = data.get("action_ids") or []
    action_ids = [str(x).strip() for x in raw_ids if str(x).strip()]
    open_playbook = bool(data.get("open_retention_playbook", False))

    return {
        "answer": answer,
        "action_ids": action_ids[:4],
        "open_retention_playbook": open_playbook,
    }


def answer_with_bedrock(
    *,
    message: str,
    segment: str,
    snippets: list[str],
) -> dict:
    """
    Returns payload with answer, actions, citations, source, model_id.
    Raises BedrockError or ValueError on failure.
    """
    if not is_bedrock_configured():
        raise BedrockError("Bedrock is not configured", status_code=503)

    raw, model_id = invoke_text(
        system_prompt=build_system_prompt(),
        user_prompt=build_user_prompt(message=message, segment=segment, snippets=snippets),
    )
    parsed = _parse_agent_json(raw)
    actions = actions_from_model_ids(
        parsed["action_ids"],
        segment=segment,
        open_retention_playbook=parsed["open_retention_playbook"],
    )
    if not actions and parsed["action_ids"]:
        actions = actions_from_model_ids(
            ["business"],
            segment=segment,
            open_retention_playbook=False,
        )

    return {
        "answer": parsed["answer"],
        "actions": actions,
        "citations": ["bedrock", *parsed["action_ids"][:4]],
        "source": "bedrock",
        "model_id": model_id,
    }
