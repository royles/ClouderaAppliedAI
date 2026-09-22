"""LLM-generated retention queue snippets (one customer per request, streaming)."""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from collections.abc import Iterator
from typing import Any

from customer360.actions.draft import classify_recommendation
from customer360.agent.locale import insight_language_instruction, normalize_ui_locale
from customer360.api.sse import sse_event
from customer360.insights.context import load_customer_context
from customer360.llm.errors import LLMError
from customer360.llm.router import is_llm_configured, stream_text_chunks

logger = logging.getLogger(__name__)

MAX_TITLE_LEN = 52
MAX_DETAIL_LEN = 130

SYSTEM_PROMPT_BASE = """You write a **retention queue** snippet for one insurance customer.
The copy appears in a narrow assistant sidebar — it must be short and scannable.

Use only facts from the customer snapshot. Cite at least one specific fact (city, policy type,
premium, foreclosure count, last login, unresolved agent question, review rating, search topic, etc.).
Avoid generic boilerplate not tied to this customer's data.

**Hard limits (strict):**
- `title`: max 52 characters — crisp action headline.
- `detail`: max 130 characters — one sentence: channel + why now for this customer.

Respond with **one JSON object only** (no markdown fences):
{ "title": "...", "detail": "..." }"""


def _clamp(text: str, max_len: int) -> str:
    cleaned = " ".join(str(text).split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "…"


def compact_snapshot(conn: sqlite3.Connection, customer_id: int) -> dict[str, Any] | None:
    ctx = load_customer_context(conn, customer_id)
    if ctx is None:
        return None
    p = ctx.payload
    policies = p.get("policies") or {}
    interactions = p.get("interactions") or {}
    foreclosures = p.get("foreclosures") or {}
    investments = p.get("investments") or {}
    return {
        "customer_id": ctx.customer_id,
        "customer_name": p.get("customer_name"),
        "city": p.get("city"),
        "preferred_communication": p.get("preferred_communication"),
        "last_login": p.get("last_login"),
        "churn_tier": ctx.churn_tier,
        "churn_probability": ctx.churn_probability,
        "active_policies": policies.get("active_policies"),
        "policy_types": (policies.get("active_policy_types") or [])[:5],
        "monthly_premium_ils": policies.get("total_monthly_premium_ils"),
        "foreclosure_count": foreclosures.get("count"),
        "investment_snapshots": investments.get("snapshot_count"),
        "events_last_90d": interactions.get("events_last_90d"),
        "unresolved_agent_questions": interactions.get("unresolved_agent_questions"),
        "avg_review_rating_90d": interactions.get("avg_review_rating"),
        "help_search_share": interactions.get("help_search_share"),
        "recent_highlights": (p.get("recent_interaction_highlights") or [])[:4],
    }


def parse_single_action_json(raw: str, customer_id: int) -> dict:
    stripped = raw.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", stripped)
        if not match:
            raise ValueError("Model did not return JSON")
        data = json.loads(match.group(0))

    title = _clamp(str(data.get("title") or "").strip(), MAX_TITLE_LEN)
    detail = _clamp(str(data.get("detail") or "").strip(), MAX_DETAIL_LEN)
    if not title or not detail:
        raise ValueError("Incomplete retention action JSON from model")

    kind = classify_recommendation(f"{title} {detail}") or "llm_snippet"
    return {
        "customer_id": customer_id,
        "recommended_action": {
            "action_code": kind,
            "title": title,
            "detail": detail,
        },
    }


def stream_retention_action_events(
    conn: sqlite3.Connection,
    customer_id: int,
    *,
    locale: str | None = None,
) -> Iterator[bytes]:
    locale_norm = normalize_ui_locale(locale)
    if not is_llm_configured():
        yield sse_event(
            "error",
            {"customer_id": customer_id, "detail": "LLM not configured"},
        )
        return

    snap = compact_snapshot(conn, customer_id)
    if snap is None:
        yield sse_event(
            "error",
            {"customer_id": customer_id, "detail": "Customer not found"},
        )
        return

    yield sse_event(
        "meta",
        {"customer_id": customer_id, "llm_configured": True},
    )

    system = SYSTEM_PROMPT_BASE + insight_language_instruction(locale_norm)
    user = (
        "Generate the retention queue snippet for this customer (JSON object).\n\n"
        f"{json.dumps(snap, ensure_ascii=False, indent=2)}"
    )

    buffer: list[str] = []
    try:
        for piece in stream_text_chunks(
            system_prompt=system,
            user_prompt=user,
            json_mode=True,
        ):
            buffer.append(piece)
            yield sse_event(
                "delta",
                {"customer_id": customer_id, "text": piece},
            )
        raw = "".join(buffer)
        done = parse_single_action_json(raw, customer_id)
        yield sse_event("done", done)
    except (LLMError, ValueError) as exc:
        logger.warning("Retention stream failed for %s: %s", customer_id, exc)
        yield sse_event(
            "error",
            {"customer_id": customer_id, "detail": str(exc)},
        )
