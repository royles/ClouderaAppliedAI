"""LLM-generated retention queue snippets (compact, profile-specific)."""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from typing import Any

from customer360.actions.draft import classify_recommendation
from customer360.agent.locale import insight_language_instruction, normalize_ui_locale
from customer360.insights.context import load_customer_context
from customer360.llm.errors import LLMError
from customer360.llm.router import invoke_text, is_llm_configured

logger = logging.getLogger(__name__)

MAX_TITLE_LEN = 52
MAX_DETAIL_LEN = 130
CHUNK_SIZE = 8

SYSTEM_PROMPT_BASE = """You write **retention queue** snippets for insurance relationship managers.
Each row appears in a narrow assistant sidebar — copy must be short and scannable.

For **every** customer in the user JSON array, produce exactly one next-best-action that:
- Is **unique** within the batch (never repeat the same title or detail wording twice).
- Cites at least one **specific** fact from that customer's snapshot (city, policy type, premium,
  foreclosure count, last login, unresolved agent question, review rating, search/help topic, etc.).
- Avoids generic insurance boilerplate unless tied to a named fact from that customer.

**Hard limits (strict):**
- `title`: max 52 characters — crisp action headline.
- `detail`: max 130 characters — one sentence: channel + why now for this customer.

Respond with **one JSON object only** (no markdown fences):
{
  "items": [
    { "customer_id": <number>, "title": "...", "detail": "..." }
  ]
}

Include one item per customer_id from the input. Do not invent customers or facts not in the data."""


def _clamp(text: str, max_len: int) -> str:
    cleaned = " ".join(str(text).split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "…"


def _compact_snapshot(conn: sqlite3.Connection, customer_id: int) -> dict[str, Any] | None:
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


def _parse_batch_json(raw: str, expected_ids: set[int]) -> list[dict[str, str]]:
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

    items = data.get("items") or []
    out: list[dict[str, str]] = []
    seen: set[int] = set()
    for row in items:
        try:
            cid = int(row.get("customer_id"))
        except (TypeError, ValueError):
            continue
        if cid not in expected_ids or cid in seen:
            continue
        title = _clamp(str(row.get("title") or "").strip(), MAX_TITLE_LEN)
        detail = _clamp(str(row.get("detail") or "").strip(), MAX_DETAIL_LEN)
        if not title or not detail:
            continue
        seen.add(cid)
        kind = classify_recommendation(f"{title} {detail}") or "llm_snippet"
        out.append(
            {
                "customer_id": cid,
                "recommended_action": {
                    "action_code": kind,
                    "title": title,
                    "detail": detail,
                },
            }
        )
    return out


def _generate_chunk(
    conn: sqlite3.Connection,
    customer_ids: list[int],
    *,
    locale: str | None,
) -> list[dict]:
    snapshots: list[dict[str, Any]] = []
    for cid in customer_ids:
        snap = _compact_snapshot(conn, cid)
        if snap:
            snapshots.append(snap)
    if not snapshots:
        return []

    expected = {int(s["customer_id"]) for s in snapshots}
    system = SYSTEM_PROMPT_BASE + insight_language_instruction(locale)
    user = (
        "Generate retention queue snippets for these customers (JSON array). "
        "Match each output item to the same customer_id.\n\n"
        f"{json.dumps(snapshots, ensure_ascii=False, indent=2)}"
    )

    raw, _model = invoke_text(system_prompt=system, user_prompt=user, json_mode=True)
    parsed = _parse_batch_json(raw, expected)
    if len(parsed) < len(expected):
        missing = expected - {p["customer_id"] for p in parsed}
        logger.warning(
            "Retention queue LLM batch missing %s customer(s): %s",
            len(missing),
            sorted(missing)[:10],
        )
    return parsed


def generate_retention_recommendations_llm(
    conn: sqlite3.Connection,
    customer_ids: list[int],
    *,
    locale: str | None = None,
) -> tuple[list[dict], bool]:
    """Returns (recommendations, llm_configured). No rule templates — LLM only."""
    if not is_llm_configured():
        return [], False

    locale_norm = normalize_ui_locale(locale)
    items: list[dict] = []
    ids: list[int] = []
    seen: set[int] = set()
    for raw_id in customer_ids:
        if len(ids) >= 50:
            break
        try:
            cid = int(raw_id)
        except (TypeError, ValueError):
            continue
        if cid in seen:
            continue
        seen.add(cid)
        ids.append(cid)

    for start in range(0, len(ids), CHUNK_SIZE):
        chunk = ids[start : start + CHUNK_SIZE]
        try:
            items.extend(_generate_chunk(conn, chunk, locale=locale_norm))
        except (LLMError, ValueError) as exc:
            logger.warning("Retention queue LLM chunk failed: %s", exc)

    got = {int(row["customer_id"]) for row in items}
    for cid in ids:
        if cid in got:
            continue
        try:
            items.extend(_generate_chunk(conn, [cid], locale=locale_norm))
        except (LLMError, ValueError) as exc:
            logger.warning("Retention queue LLM retry failed for %s: %s", cid, exc)

    return items, True
