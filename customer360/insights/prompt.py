"""Prompt templates for Bedrock insight generation."""

from __future__ import annotations

import json

SYSTEM_PROMPT = """You are an insurance customer experience advisor for a Customer 360 dashboard.
Write concise, actionable guidance that improves the customer's experience and trust.
Never invent products or facts not present in the customer data.
Respond with a single JSON object only (no markdown fences), using this schema:
{
  "summary": "2-3 short sentences on the customer's relationship and engagement",
  "primary_focus": "upsell" or "retention",
  "recommendations": ["3 to 5 bullet strings, each under 120 characters"],
  "experience_note": "one sentence on the best next touchpoint for this customer"
}
Rules:
- If churn risk is LOW, set primary_focus to upsell and emphasize growth and value-add.
- If churn risk is MEDIUM, balance retention hygiene with modest upsell where appropriate.
- If churn risk is HIGH, set primary_focus to retention and prioritize empathy, stability, and proactive service.
- If churn data is missing, infer cautiously from engagement signals (login, policies, foreclosures).
- Use interaction events (reviews, agent questions, product/help searches) to tailor tone and next steps.
- Reference unresolved agent questions or help searches when recommending retention actions.
- Reference positive reviews or product searches when recommending upsell actions.
- Keep every string plain language, specific to the data, and customer-centric (not sales jargon).
"""


def focus_instruction(churn_tier: str | None) -> str:
    tier = (churn_tier or "UNKNOWN").upper()
    if tier == "HIGH":
        return (
            "Churn risk is HIGH — lead with retention: reduce friction, rebuild confidence, "
            "and address stress signals (foreclosures, inactivity) before any upsell."
        )
    if tier == "MEDIUM":
        return (
            "Churn risk is MEDIUM — stabilize the relationship first, then suggest one relevant "
            "upsell only if it clearly improves coverage or savings."
        )
    if tier == "LOW":
        return (
            "Churn risk is LOW — prioritize thoughtful upsell and cross-sell that deepen value "
            "and simplify the customer's portfolio."
        )
    return (
        "Churn score unavailable — focus on engagement quality; suggest upsell only when "
        "supported by active policies and recent login."
    )


def build_user_prompt(payload: dict, churn_tier: str | None) -> str:
    return (
        f"{focus_instruction(churn_tier)}\n\n"
        "Customer warehouse snapshot (JSON):\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
