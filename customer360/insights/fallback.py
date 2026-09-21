"""Rule-based insights when Bedrock is unavailable."""

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

    if tier == "HIGH":
        primary = "retention"
        summary = (
            f"{name} shows elevated churn risk with {active} active policy(ies). "
            f"Prioritize reassurance, clear next steps, and responsive service."
        )
        recs = [
            "Schedule a proactive check-in within 7 days to review coverage and open questions.",
            "Confirm preferred channel and send a plain-language summary of active policies.",
        ]
        if fc_count:
            recs.append(
                "Acknowledge foreclosure records sensitively and offer a dedicated support path."
            )
        if not login:
            recs.append(
                "Invite them back to the digital portal with a guided tour of self-service tools."
            )
        if unresolved:
            recs.append(
                "Close open agent questions first — assign an owner and confirm resolution in writing."
            )
        if help_share is not None and help_share >= 0.5:
            recs.append(
                "Address recent help-center themes (payments, cancellation) before any product pitch."
            )
        recs.append(
            "Pause aggressive upsell; offer only fixes that reduce cost or simplify payments."
        )
        experience = "A warm outbound call or secure message works best to rebuild trust quickly."
    elif tier == "MEDIUM":
        primary = "retention"
        summary = (
            f"{name} is in a watch zone with moderate churn signals across {active} active policies. "
            "Strengthen engagement before expanding the relationship."
        )
        recs = [
            "Send a personalized policy health summary highlighting gaps and savings options.",
            "Use last-login timing to nudge digital engagement with one clear action.",
            "Offer a brief review of investment performance if accumulation is material.",
            "Introduce one relevant add-on only if it closes a documented coverage gap.",
        ]
        if unresolved:
            recs.insert(0, "Resolve outstanding agent conversations to prevent silent churn.")
        if avg_rating is not None and avg_rating <= 3:
            recs.append("Follow up on recent reviews with a service recovery note.")
        experience = "A concise email plus optional callback link balances respect for their time."
    else:
        primary = "upsell"
        summary = (
            f"{name} appears engaged with {active} active policy(ies) and lower churn risk. "
            "Focus on deepening value and simplifying their insurance portfolio."
        )
        recs = [
            "Bundle complementary coverage where types already span life, health, or pension.",
            "Highlight investment track options aligned with recent accumulation trends.",
            "Propose premium optimization for long-tenure active policies.",
            "Invite them to a digital planning session to consolidate policies in one view.",
        ]
        if int(investments.get("snapshot_count") or 0) > 0:
            recs.append(
                "Share a short performance snapshot with plain-language explanations of YTD movement."
            )
        if avg_rating is not None and avg_rating >= 4:
            recs.append(
                "Leverage strong recent reviews — suggest one upgrade tied to product searches they explored."
            )
        experience = "Lead with a value-forward digital message and an easy one-click follow-up."

    recs = recs[:5]
    return {
        "summary": summary,
        "primary_focus": primary,
        "recommendations": recs,
        "experience_note": experience,
    }
