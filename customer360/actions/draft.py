"""Classify insight text and draft channel-ready messages via Amazon Bedrock."""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone

from customer360.actions.bedrock_draft import generate_communication_draft
from customer360.llm.errors import LLMError
from customer360.llm.router import is_llm_configured
from customer360.llm_provider import get_active_provider, provider_label
from customer360.insights.context import load_customer_context


def classify_recommendation(text: str) -> str | None:
    """Return action kind or None if not simulatable."""
    t = text.lower()
    if re.search(r"\b(call|check-in|outbound|phone)\b", t):
        return "call_script"
    if "portal" in t or "digital" in t or "login" in t or "self-service" in t:
        return "email_portal_invite"
    if "service recovery" in t or ("review" in t and "follow up" in t):
        return "email_service_recovery"
    if "performance" in t or "investment" in t or "accumulation" in t or "ytd" in t:
        return "email_investment_summary"
    if "policy health" in t or ("personalized" in t and "policy" in t) or (
        "plain-language summary" in t and "polic" in t
    ):
        return "email_policy_summary"
    if "callback" in t or ("concise email" in t and "email" in t):
        return "email_with_callback"
    if re.search(r"\b(send|email|message)\b", t):
        return "email_general"
    if "sms" in t or "text message" in t:
        return "sms_nudge"
    return None


def channel_for_action_kind(action_kind: str) -> str:
    if action_kind == "call_script":
        return "call"
    if action_kind == "sms_nudge":
        return "sms"
    return "email"


def build_action_draft(
    conn: sqlite3.Connection,
    customer_id: int,
    recommendation: str,
    *,
    source: str = "recommendation",
) -> dict:
    ctx = load_customer_context(conn, customer_id)
    if ctx is None:
        raise ValueError("Customer not found")

    action_kind = classify_recommendation(recommendation)
    if source == "experience_note" and not action_kind:
        action_kind = classify_recommendation(recommendation) or (
            "email_with_callback" if "email" in recommendation.lower() else "call_script"
        )

    if not action_kind:
        return {
            "actionable": False,
            "recommendation": recommendation,
            "message": "This recommendation is advisory only — no automated draft is available.",
            "content_source": None,
        }

    if not is_llm_configured():
        return {
            "actionable": False,
            "recommendation": recommendation,
            "action_kind": action_kind,
            "message": (
                "Communication drafts require a configured LLM backend. "
                "Use Data & Admin → Configuration → LLM provider (Bedrock or OpenAI-compatible)."
            ),
            "content_source": None,
            "bedrock_required": True,
        }

    email_row = conn.execute(
        "SELECT CUSTOMER_NAME, EMAIL, MOBILE_NO FROM DWH_DIM_CUSTOMERS_UNIQUE "
        "WHERE CURRENT_IND = 1 AND CUSTOMER_ID = ?",
        (customer_id,),
    ).fetchone()
    name = ctx.payload.get("customer_name") or "Customer"
    email = None
    phone = None
    if email_row is not None:
        keys = email_row.keys() if hasattr(email_row, "keys") else []
        if "CUSTOMER_NAME" in keys and email_row["CUSTOMER_NAME"]:
            name = email_row["CUSTOMER_NAME"]
        email = email_row["EMAIL"] if "EMAIL" in keys else None
        phone = email_row["MOBILE_NO"] if "MOBILE_NO" in keys else None

    expected_channel = channel_for_action_kind(action_kind)
    channel_labels = {
        "email": "Draft email (Bedrock)",
        "sms": "Draft SMS (Bedrock)",
        "call": "Call script (Bedrock)",
    }

    try:
        generated, model_id = generate_communication_draft(
            customer_payload=ctx.payload,
            customer_id=customer_id,
            recommendation=recommendation,
            action_kind=action_kind,
            expected_channel=expected_channel,
        )
    except (LLMError, ValueError) as exc:
        return {
            "actionable": False,
            "recommendation": recommendation,
            "action_kind": action_kind,
            "message": f"LLM could not generate this draft: {exc}",
            "content_source": "bedrock_error",
            "generation_error": str(exc),
        }

    llm_provider = get_active_provider()
    draft_source = "openai_compatible" if llm_provider == "openai_compatible" else "bedrock"
    provider_name = provider_label(llm_provider)

    return {
        "actionable": True,
        "action_kind": action_kind,
        "channel": generated["channel"],
        "preview_label": channel_labels.get(generated["channel"], f"Draft ({provider_name})"),
        "recommendation": recommendation,
        "subject": generated.get("subject"),
        "body": generated["body"],
        "recipient_name": name,
        "recipient_email": email,
        "recipient_phone": phone,
        "content_source": draft_source,
        "model_id": model_id,
    }


def simulate_send(channel: str, *, subject: str | None, body: str, customer_id: int) -> dict:
    sent_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    if channel == "email":
        detail = f"Email queued to customer {customer_id} (Bedrock-generated body)"
        if subject:
            detail += f" — subject: {subject[:80]}"
    elif channel == "sms":
        detail = f"SMS queued to customer {customer_id} ({len(body)} chars, Bedrock-generated)"
    else:
        detail = f"Call script logged for customer {customer_id} (Bedrock-generated)"

    return {
        "status": "simulated",
        "channel": channel,
        "sent_at": sent_at,
        "message": detail,
    }
