"""Classify insight text and draft channel-ready messages from warehouse data."""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone

from customer360.insights.context import load_customer_context
from customer360.interactions.summary import load_interaction_bundle


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


def _active_policies(conn: sqlite3.Connection, customer_id: int) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return conn.execute(
        """
        SELECT POLICY_NUM, POLICY_TYPE_DESC, POLICY_STATUS_DESC, BRUTO_MONTHLY_PREMIUM, IS_ACTIVE
        FROM DWH_DIM_ALL_POLICY
        WHERE CUSTOMER_ID = ?
        ORDER BY IS_ACTIVE DESC, POLICY_NUM
        """,
        (str(customer_id),),
    ).fetchall()


def _format_money(amount: float | None) -> str:
    if amount is None:
        return "—"
    return f"₪{amount:,.0f}"


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

    profile = ctx.payload
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
        }

    policies = _active_policies(conn, customer_id)
    interactions = load_interaction_bundle(conn, customer_id, limit=5)

    name = profile.get("customer_name") or "Customer"
    email_row = conn.execute(
        "SELECT EMAIL, MOBILE_NO, COMMUNICATION_DSC FROM DWH_DIM_CUSTOMERS_UNIQUE "
        "WHERE CURRENT_IND = 1 AND CUSTOMER_ID = ?",
        (customer_id,),
    ).fetchone()
    email = email_row["EMAIL"] if email_row else None
    phone = email_row["MOBILE_NO"] if email_row else None
    comm = email_row["COMMUNICATION_DSC"] if email_row else profile.get("preferred_communication")

    active_lines = [
        f"  • Policy {p['POLICY_NUM']}: {p['POLICY_TYPE_DESC'] or 'Policy'} — "
        f"{p['POLICY_STATUS_DESC'] or 'Status unknown'}, "
        f"premium {_format_money(p['BRUTO_MONTHLY_PREMIUM'])}"
        for p in policies
        if p["IS_ACTIVE"]
    ]
    policy_block = "\n".join(active_lines) if active_lines else "  • No active policies on file."

    churn_tier = (profile.get("churn") or {}).get("risk_tier") or "UNKNOWN"
    city = profile.get("city") or "your area"
    last_login = profile.get("last_login") or "not recorded recently"

    subject = f"Your insurance update — {name.split()[0] if name else 'Customer'}"
    body = ""
    channel = "email"

    if action_kind == "call_script":
        channel = "call"
        subject = None
        open_items = interactions["summary"].get("unresolved_agent_questions", 0)
        body = (
            f"Call script — {name} (ID {customer_id})\n\n"
            f"Opening: Hello {name.split()[0]}, this is [Agent] from Customer Care. "
            f"I'm calling for a brief check-in on your policies.\n\n"
            f"Context: Churn tier {churn_tier}. Preferred contact: {comm}. "
            f"Last portal login: {last_login}.\n\n"
            f"Active coverage:\n{policy_block}\n\n"
        )
        if open_items:
            body += f"Note: {open_items} open agent question(s) — confirm resolution on the call.\n\n"
        body += (
            "Close: Summarize next steps, confirm email/phone, and offer a follow-up in writing.\n"
        )
    elif action_kind == "email_portal_invite":
        subject = "Quick access to your policy portal"
        body = (
            f"Dear {name},\n\n"
            f"We noticed it has been a while since your last login ({last_login}). "
            f"Your portal brings together policies, documents, and messages in one place.\n\n"
            f"Your active policies:\n{policy_block}\n\n"
            f"Sign in: https://portal.example.co.il/login?customer={customer_id}\n\n"
            f"If you prefer {comm or 'email'}, reply and we will walk you through the first step.\n\n"
            f"Warm regards,\nCustomer Care Team"
        )
    elif action_kind == "email_policy_summary":
        subject = "Your personalized policy health summary"
        body = (
            f"Dear {name},\n\n"
            f"Following our review of your account in {city}, here is a plain-language "
            f"snapshot of your coverage and suggested next steps.\n\n"
            f"Active policies:\n{policy_block}\n\n"
            f"Engagement: last login {last_login}. "
            f"Our goal is to simplify your portfolio and highlight any gaps or savings.\n\n"
            f"Reply to this message or book a 15-minute review: "
            f"https://portal.example.co.il/book?customer={customer_id}\n\n"
            f"Best regards,\nYour insurance advisor"
        )
    elif action_kind == "email_investment_summary":
        inv = profile.get("investments") or {}
        subject = "Investment performance snapshot"
        body = (
            f"Dear {name},\n\n"
            f"Below is a concise view of your latest investment snapshots on file.\n\n"
            f"Total accumulation (latest snapshots): {_format_money(inv.get('total_accumulation_ils'))}\n"
            f"Year-to-date P/L (aggregated): {_format_money(inv.get('total_ytd_pl_ils'))}\n\n"
            f"Active policies linked to savings/pension:\n{policy_block}\n\n"
            f"Questions? Reply here or call us at 1-800-555-0199 (simulated).\n\n"
            f"Regards,\nInvestments Service Desk"
        )
    elif action_kind == "email_service_recovery":
        rating = interactions["summary"].get("avg_review_rating")
        subject = "Thank you — we're following up on your feedback"
        body = (
            f"Dear {name},\n\n"
            f"Thank you for sharing feedback about your recent experience"
            f"{f' (recent average rating {rating}/5)' if rating else ''}. "
            f"We want to make this right and prevent repeat friction.\n\n"
            f"Your advisor will personally review your open policies:\n{policy_block}\n\n"
            f"Please reply with a good time to connect, or use this callback link: "
            f"https://portal.example.co.il/callback?customer={customer_id}\n\n"
            f"Sincerely,\nCustomer Experience Team"
        )
    elif action_kind == "email_with_callback":
        subject = "Short update and optional callback"
        body = (
            f"Dear {name},\n\n"
            f"We have a concise update on your account — no action required unless you want to talk.\n\n"
            f"Coverage summary:\n{policy_block}\n\n"
            f"Optional callback (pick a slot): "
            f"https://portal.example.co.il/callback?customer={customer_id}\n"
            f"Or reply to this email and we will call you at {phone or 'the number on file'}.\n\n"
            f"Thank you,\nCustomer Care"
        )
    elif action_kind == "sms_nudge":
        channel = "sms"
        subject = None
        body = (
            f"Hi {name.split()[0]}, Customer 360: you have {len(active_lines)} active policy(ies). "
            f"View details: https://portal.example.co.il/m/{customer_id} Reply STOP to opt out."
        )
    else:
        subject = "Message from your insurance team"
        body = (
            f"Dear {name},\n\n"
            f"Regarding: {recommendation}\n\n"
            f"Account snapshot:\n{policy_block}\n\n"
            f"Preferred channel on file: {comm}. Last login: {last_login}.\n\n"
            f"Reply if you would like us to take the next step together.\n\n"
            f"Best,\nCustomer Care"
        )

    channel_labels = {
        "email": "Draft email",
        "sms": "Draft SMS",
        "call": "Call script",
    }

    return {
        "actionable": True,
        "action_kind": action_kind,
        "channel": channel,
        "preview_label": channel_labels.get(channel, "Draft message"),
        "recommendation": recommendation,
        "subject": subject,
        "body": body,
        "recipient_name": name,
        "recipient_email": email,
        "recipient_phone": phone,
    }


def simulate_send(channel: str, *, subject: str | None, body: str, customer_id: int) -> dict:
    sent_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    if channel == "email":
        detail = f"Email queued to customer {customer_id}"
        if subject:
            detail += f" — subject: {subject[:80]}"
    elif channel == "sms":
        detail = f"SMS queued to customer {customer_id} ({len(body)} chars)"
    else:
        detail = f"Call script logged for customer {customer_id} (no outbound dial in demo)"

    return {
        "status": "simulated",
        "channel": channel,
        "sent_at": sent_at,
        "message": detail,
    }
