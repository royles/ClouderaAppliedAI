"""Generate outreach drafts via Amazon Bedrock."""

from __future__ import annotations

import json
import re

from customer360.llm.router import invoke_text

ACTION_DRAFT_SYSTEM = """## Role
You draft outbound communications for an insurance Customer 360 workspace. The reader is the
customer; the writer is Customer Care on behalf of their relationship manager.

## Tone
Warm, concise, professional — plain language, no jargon, no pressure. Use only facts from the
provided customer JSON.

## Output
Return one JSON object only. No markdown fences, no text before or after the JSON:
{
  "channel": "email" | "sms" | "call",
  "subject": "string or null (null for sms/call)",
  "body": "full message text; for call scripts use labeled sections agents can read aloud"
}

## Rules
- Match the requested channel and action intent from the user message.
- Email: greeting with customer name, clear next step, sign-off from Customer Care.
- SMS: under 320 characters; include https://portal.example.co.il/m/{customer_id}.
- Call script: Opening, Context, Talking points, Close (plain text, not JSON inside body).
- Reference churn tier and recent interactions when relevant.
- Never include full credit card or password data.
"""


def _load_first_json_object(text: str) -> dict:
    """Parse the first JSON object; tolerate trailing prose or a second JSON blob."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped.strip())
    try:
        data, _end = json.JSONDecoder().raw_decode(stripped)
    except json.JSONDecodeError as exc:
        start = stripped.find("{")
        if start < 0:
            raise ValueError("Model did not return JSON for the draft") from exc
        try:
            data, _end = json.JSONDecoder().raw_decode(stripped[start:])
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", stripped)
            if not match:
                raise ValueError("Model did not return JSON for the draft") from exc
            data, _end = json.JSONDecoder().raw_decode(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("Draft JSON must be an object")
    return data


def _parse_draft_json(text: str) -> dict:
    data = _load_first_json_object(text)
    channel = str(data.get("channel", "")).strip().lower()
    if channel not in ("email", "sms", "call"):
        raise ValueError(f"Invalid channel in draft JSON: {channel!r}")
    body = str(data.get("body", "")).strip()
    if not body:
        raise ValueError("Draft body is empty")
    subject = data.get("subject")
    if subject is not None:
        subject = str(subject).strip() or None
    if channel in ("sms", "call"):
        subject = None
    return {"channel": channel, "subject": subject, "body": body}


def generate_communication_draft(
    *,
    customer_payload: dict,
    customer_id: int,
    recommendation: str,
    action_kind: str,
    expected_channel: str,
) -> tuple[dict, str]:
    """Return parsed draft fields and catalog model id."""
    user_prompt = (
        f"Customer ID: {customer_id}\n"
        f"Action type: {action_kind}\n"
        f"Required channel: {expected_channel}\n"
        f"Insight recommendation to execute:\n{recommendation}\n\n"
        "Customer data (JSON):\n"
        f"{json.dumps(customer_payload, ensure_ascii=False, indent=2)}"
    )
    raw, model_id = invoke_text(
        system_prompt=ACTION_DRAFT_SYSTEM,
        user_prompt=user_prompt,
        json_mode=True,
    )
    parsed = _parse_draft_json(raw)
    if parsed["channel"] != expected_channel:
        parsed["channel"] = expected_channel
    return parsed, model_id
