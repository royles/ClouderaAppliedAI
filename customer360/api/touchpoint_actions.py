"""Recommended next touchpoint actions from churn tier and interaction signals."""

from __future__ import annotations

from typing import Any


def recommended_touchpoint_action(row: dict[str, Any]) -> dict[str, str]:
    """Same rules as the engagement hub — one primary outreach lever per customer."""
    unresolved = int(row.get("unresolved_agent_questions") or 0)
    days_since = float(row.get("days_since_last_interaction") or 999)
    web_90 = int(row.get("web_search_90d") or 0)
    reviews_90 = int(row.get("review_count_90d") or 0)
    tier = (row.get("churn_risk_tier") or "").upper()
    events_90 = int(row.get("events_last_90d") or 0)

    if unresolved > 0:
        return {
            "action_code": "resolve_agent_question",
            "title": "Resolve open agent question",
            "detail": f"{unresolved} unresolved question(s) in the last 90 days — call or message while context is fresh.",
            "channel_hint": "phone",
        }
    if tier == "HIGH" and events_90 >= 1:
        return {
            "action_code": "retention_call",
            "title": "Retention call (channel is warm)",
            "detail": "High churn risk but recent touchpoints — prioritize a human retention conversation.",
            "channel_hint": "phone",
        }
    if days_since >= 90:
        return {
            "action_code": "reengagement_outreach",
            "title": "Re-engagement outreach",
            "detail": "No recent contact — send a personalized check-in (email or SMS) and offer a digital review.",
            "channel_hint": "email",
        }
    if web_90 >= 2 and reviews_90 == 0:
        return {
            "action_code": "invite_review",
            "title": "Invite feedback after digital research",
            "detail": "Customer is searching products/help online — ask for a quick review or satisfaction pulse.",
            "channel_hint": "email",
        }
    if tier == "HIGH":
        return {
            "action_code": "retention_call",
            "title": "Priority retention call",
            "detail": "High lapse risk — lead with empathy and payment/coverage options before any upsell.",
            "channel_hint": "phone",
        }
    if tier == "MEDIUM":
        return {
            "action_code": "proactive_review",
            "title": "Proactive policy review",
            "detail": "Schedule a review before renewal; address open questions from digital touchpoints.",
            "channel_hint": "phone",
        }
    return {
        "action_code": "relationship_review",
        "title": "Schedule relationship review",
        "detail": "Stable engagement — book a proactive review to discuss coverage and savings goals.",
        "channel_hint": "phone",
    }
