"""Orchestrate insight generation, cache, Bedrock, and fallback."""

from __future__ import annotations

import json
import logging
import re
import sqlite3

from customer360.llm.errors import LLMError
from customer360.llm.router import invoke_text, is_llm_configured
from customer360.llm_provider import get_active_provider
from customer360.insights.cache import load_cached, save_cached
from customer360.insights.context import load_customer_context
from customer360.insights.fallback import generate_fallback
from customer360.insights.prompt import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


def _parse_model_json(text: str) -> dict:
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
    summary = str(data.get("summary", "")).strip()
    primary = str(data.get("primary_focus", "")).strip().lower()
    if primary not in ("upsell", "retention"):
        primary = "retention" if primary.startswith("ret") else "upsell"
    recs_raw = data.get("recommendations") or []
    recommendations = [str(r).strip() for r in recs_raw if str(r).strip()][:5]
    experience = str(data.get("experience_note", "")).strip()
    if not summary or not recommendations:
        raise ValueError("Incomplete insight JSON from model")
    return {
        "summary": summary,
        "primary_focus": primary,
        "recommendations": recommendations,
        "experience_note": experience,
    }


def _align_focus_with_churn(parsed: dict, churn_tier: str | None) -> dict:
    tier = (churn_tier or "").upper()
    if tier == "HIGH":
        parsed["primary_focus"] = "retention"
    elif tier == "LOW":
        parsed["primary_focus"] = "upsell"
    return parsed


def get_customer_insights(
    conn: sqlite3.Connection,
    customer_id: int,
    *,
    refresh: bool = False,
) -> dict | None:
    ctx = load_customer_context(conn, customer_id)
    if ctx is None:
        return None

    llm_ready = is_llm_configured()

    if not refresh:
        cached = load_cached(conn, customer_id, ctx.context_hash)
        if cached:
            stale_fallback = llm_ready and cached.get("source") == "fallback"
            if not stale_fallback:
                cached["bedrock_configured"] = llm_ready
                cached["cached"] = True
                cached.setdefault("experience_note", "")
                cached.setdefault("fallback_reason", None)
                return cached

    parsed: dict
    source: str
    model_id: str | None = None
    fallback_reason: str | None = None

    if llm_ready:
        try:
            raw, model_id = invoke_text(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=build_user_prompt(ctx.payload, ctx.churn_tier),
            )
            parsed = _align_focus_with_churn(_parse_model_json(raw), ctx.churn_tier)
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

    generated_at = save_cached(
        conn,
        customer_id,
        ctx.context_hash,
        summary=parsed["summary"],
        primary_focus=parsed["primary_focus"],
        recommendations=parsed["recommendations"],
        experience_note=parsed.get("experience_note", ""),
        source=source,
        model_id=model_id,
        fallback_reason=fallback_reason,
    )

    return {
        "summary": parsed["summary"],
        "primary_focus": parsed["primary_focus"],
        "recommendations": parsed["recommendations"],
        "experience_note": parsed.get("experience_note", ""),
        "source": source,
        "model_id": model_id,
        "generated_at": generated_at,
        "bedrock_configured": llm_ready,
        "fallback_reason": fallback_reason,
        "cached": False,
    }
