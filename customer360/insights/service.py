"""Orchestrate insight generation (always fresh — no read-through cache)."""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone

from customer360.llm.errors import LLMError
from customer360.llm.router import invoke_text, is_llm_configured
from customer360.llm_provider import get_active_provider
from customer360.insights.context import load_customer_context
from customer360.insights.fallback import generate_fallback
from customer360.insights.parse import parse_insight_json
from customer360.insights.prompt import build_insight_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)


def _align_focus_with_churn(parsed: dict, churn_tier: str | None) -> dict:
    tier = (churn_tier or "").upper()
    if tier == "HIGH":
        parsed["primary_focus"] = "retention"
    elif tier == "LOW":
        parsed["primary_focus"] = "upsell"
    return parsed


def _generated_at_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def get_customer_insights(
    conn: sqlite3.Connection,
    customer_id: int,
    *,
    refresh: bool = False,
    locale: str | None = None,
) -> dict | None:
    del refresh  # kept for API compatibility; insights are always regenerated
    ctx = load_customer_context(conn, customer_id)
    if ctx is None:
        return None

    llm_ready = is_llm_configured()
    parsed: dict
    source: str
    model_id: str | None = None
    fallback_reason: str | None = None

    if llm_ready:
        try:
            raw, model_id = invoke_text(
                system_prompt=build_insight_system_prompt(locale),
                user_prompt=build_user_prompt(ctx.payload, ctx.churn_tier),
                json_mode=True,
            )
            parsed = _align_focus_with_churn(parse_insight_json(raw), ctx.churn_tier)
            provider = get_active_provider()
            source = "openai_compatible" if provider == "openai_compatible" else "bedrock"
        except (LLMError, ValueError) as exc:
            logger.warning("LLM insight generation failed: %s", exc)
            fallback_reason = str(exc)
            parsed = generate_fallback(ctx.payload)
            source = "fallback"
    else:
        parsed = generate_fallback(ctx.payload)
        source = "fallback"

    return {
        "preamble": parsed.get("preamble", ""),
        "summary": parsed["summary"],
        "guidance": parsed.get("guidance", ""),
        "primary_focus": parsed["primary_focus"],
        "recommendations": parsed["recommendations"],
        "experience_note": parsed.get("experience_note", ""),
        "source": source,
        "model_id": model_id,
        "generated_at": _generated_at_stamp(),
        "bedrock_configured": llm_ready,
        "fallback_reason": fallback_reason,
        "cached": False,
    }
