"""Rule-based insights when the LLM is unavailable."""

from __future__ import annotations


def _tier(churn_tier: str | None) -> str:
    return (churn_tier or "UNKNOWN").upper()


def generate_fallback(payload: dict) -> dict:
    name = payload.get("customer_name") or "This customer"
    policies = payload.get("policies") or {}
    investments = payload.get("investments") or {}
    foreclosures = payload.get("foreclosures") or {}
    churn = payload.get("churn") or {}
    interactions = payload.get("interactions") or {}
    tier = _tier(churn.get("risk_tier"))

    active = int(policies.get("active_policies") or 0)
    login = payload.get("last_login")
    fc_count = int(foreclosures.get("count") or 0)
    unresolved = int(interactions.get("unresolved_agent_questions") or 0)
    avg_rating = interactions.get("avg_review_rating")
    help_share = interactions.get("help_search_share")
    city = payload.get("city") or "their area"

    if tier == "HIGH":
        primary = "retention"
        preamble = f"{name} needs careful attention right now."
        summary = (
            f"{name} shows elevated churn risk with {active} active policy(ies). "
            f"Prioritize reassurance, clear next steps, and responsive service."
        )
        guidance = (
            f"Start from what they can see today: {active} active policies and signals from "
            f"{city}. Acknowledge any stress calmly — especially if foreclosure records or "
            f"long gaps since login appear in the file — before discussing changes to coverage.\n\n"
            f"Close loops on service first. "
            + (
                f"There are {unresolved} open agent question(s) in the last 90 days; assign an "
                f"owner and confirm resolution in writing before any product conversation. "
                if unresolved
                else "Confirm they know how to reach a single point of contact for billing and claims. "
            )
            + (
                "Recent help-center activity suggests payment or cancellation themes — address "
                "those plainly in your next message. "
                if help_share is not None and help_share >= 0.5
                else ""
            )
            + "Hold off on aggressive upsell until trust feels restored."
        )
        recs = [
            "Schedule a proactive check-in call within seven days to review coverage and open questions.",
            "Send a plain-language email summary of active policies and the best number to call for help.",
        ]
        if fc_count:
            recs.append(
                "Acknowledge foreclosure records sensitively and offer a dedicated support path."
            )
        if not login:
            recs.append(
                "Invite them back to the digital portal with a short guided tour of self-service tools."
            )
        experience = "A warm outbound call or secure message works best to rebuild trust quickly."
    elif tier == "MEDIUM":
        primary = "retention"
        preamble = f"{name} is in a watch zone — small gestures matter."
        summary = (
            f"{name} is in a watch zone with moderate churn signals across {active} active policies. "
            "Strengthen engagement before expanding the relationship."
        )
        guidance = (
            f"They maintain {active} active policies; use that stability as the opening. "
            f"Reference their preferred communication channel when you reach out from {city}.\n\n"
            "Offer a concise policy health review that highlights gaps and savings, tied to their "
            "last login pattern. Introduce at most one add-on if it closes a documented gap — "
            "not a broad catalog pitch."
        )
        recs = [
            "Send a personalized email with a policy health summary highlighting gaps and savings options.",
            "Use last-login timing to nudge digital engagement with one clear action.",
            "Offer a brief review of investment performance if accumulation is material.",
        ]
        if unresolved:
            recs.insert(0, "Resolve outstanding agent conversations before proposing any add-on.")
        if avg_rating is not None and avg_rating <= 3:
            recs.append("Follow up on recent reviews with a service recovery email.")
        experience = "A concise email plus optional callback link balances respect for their time."
    else:
        primary = "upsell"
        preamble = f"{name} looks like a strong candidate for thoughtful growth."
        summary = (
            f"{name} appears engaged with {active} active policy(ies) and lower churn risk. "
            "Focus on deepening value and simplifying their insurance portfolio."
        )
        guidance = (
            f"With {active} active policies and lower churn risk, lead with clarity and convenience. "
            f"Connect any recent product or help searches to a single coherent story about simplifying "
            f"their portfolio in {city}.\n\n"
            "When investments are present, a short performance snapshot in plain language builds "
            "credibility. Pair growth ideas with an easy next step — digital or human — rather than "
            "a wide menu of products."
        )
        recs = [
            "Send an email proposing bundled complementary coverage where types already span life, health, or pension.",
            "Invite them to a digital planning session to consolidate policies in one view.",
        ]
        if int(investments.get("snapshot_count") or 0) > 0:
            recs.append(
                "Email a short investment performance snapshot with plain-language YTD movement."
            )
        if avg_rating is not None and avg_rating >= 4:
            recs.append(
                "Leverage strong recent reviews — suggest one upgrade tied to product searches they explored."
            )
        experience = "Lead with a value-forward digital message and an easy one-click follow-up."

    recs = recs[:5]
    return {
        "preamble": preamble,
        "summary": summary,
        "primary_focus": primary,
        "guidance": guidance,
        "recommendations": recs,
        "experience_note": experience,
    }
