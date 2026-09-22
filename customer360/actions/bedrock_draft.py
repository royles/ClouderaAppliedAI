"""Generate outreach drafts via Amazon Bedrock."""

from __future__ import annotations

import json
import re

from customer360.llm.router import invoke_text

ACTION_DRAFT_SYSTEM = """You draft customer communications for an insurance Customer 360 workspace.
Use ONLY facts from the provided customer JSON. Do not invent policies, amounts, or products.
Write warm, concise, professional copy focused on the customer's experience.
Respond with a single JSON object only (no markdown fences):
{
  "channel": "email" | "sms" | "call",
  "subject": "string or null (null for sms/call)",
  "body": "full message text; for call scripts include Opening, Context, Talking points, Close"
}
Rules:
- Match the requested channel and action intent.
- Email: include greeting using the customer's name, clear next step, sign-off from Customer Care.
- SMS: under 320 characters, include simulated portal link https://portal.example.co.il/m/{customer_id}.
- Call script: bullet-style sections agents can read aloud.
- Reference churn tier and recent interactions when relevant to tone.
- Never include full credit card or password data.
"""


def _parse_draft_json(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        match = re.search(r"\{[\s\S]*\}", stripped)
        if not match:
            raise ValueError("Bedrock did not return JSON for the draft") from exc
        data = json.loads(match.group(0))
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
    raw, model_id = invoke_text(system_prompt=ACTION_DRAFT_SYSTEM, user_prompt=user_prompt)
    parsed = _parse_draft_json(raw)
    if parsed["channel"] != expected_channel:
        parsed["channel"] = expected_channel
    return parsed, model_id
