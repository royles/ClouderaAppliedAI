"""Rule-based intent routing (no LLM). Returns narrative + validated navigation actions."""

from __future__ import annotations

import re
import sqlite3
from urllib.parse import urlencode

from customer360.agent.catalog import CATALOG, CatalogEntry, ENTRY_BY_ID
from customer360.api.segments import normalize_segment

_WORD = re.compile(r"[a-z0-9']+")


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def _score_entry(entry: CatalogEntry, text: str, tokens: set[str]) -> int:
    score = 0
    for phrase in entry.phrases:
        if phrase in text:
            score += 10 + len(phrase.split())
    for phrase in entry.phrases:
        for word in phrase.split():
            if word in tokens:
                score += 1
    return score


def _pick_entry(text: str) -> CatalogEntry | None:
    tokens = _tokens(text)
    best: CatalogEntry | None = None
    best_score = 0
    for entry in CATALOG:
        s = _score_entry(entry, text, tokens)
        if s > best_score:
            best_score = s
            best = entry
    return best if best_score >= 2 else None


def _overview_snippet(conn: sqlite3.Connection) -> str | None:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_OVERVIEW_COUNTS'"
    ).fetchone()
    if not row:
        return None
    customers = conn.execute(
        """
        SELECT ROW_COUNT FROM APP_OVERVIEW_COUNTS
        WHERE FILTER_KEY = 'customers_all' LIMIT 1
        """
    ).fetchone()
    if not customers:
        return None
    n = int(customers[0])
    return f"The book has {n:,} current customers in the overview."


def _portfolio_snippet(conn: sqlite3.Connection, segment: str) -> str | None:
    from customer360.api.portfolio_analytics import fetch_portfolio_analytics

    try:
        payload = fetch_portfolio_analytics(conn, segment=segment)
    except Exception:
        return None
    kpis = payload.get("kpis") or {}
    book = kpis.get("total_book_value")
    risk = kpis.get("value_at_risk_12m")
    retention = kpis.get("annual_retention_rate_forecast")
    parts: list[str] = []
    if book is not None:
        parts.append(f"total book value about ₪{float(book):,.0f}")
    if retention is not None:
        parts.append(f"12m retention forecast {float(retention) * 100:.1f}%")
    if risk is not None:
        parts.append(f"value at churn risk about ₪{float(risk):,.0f}")
    if not parts:
        return None
    seg_label = segment.replace("_", " ")
    return f"For {seg_label}: {', '.join(parts)}."


def _action_navigate(entry: CatalogEntry, *, segment: str | None = None) -> dict:
    search = entry.search
    if segment and entry.entry_id in ("business", "retention_playbook"):
        params = {}
        if entry.search:
            for part in entry.search.split("&"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    params[k] = v
        if segment != "customers_all":
            params["segment"] = segment
        search = urlencode(params)
    return {
        "action_id": entry.entry_id,
        "label": f"Open {entry.title}",
        "action_type": "navigate",
        "path": entry.path,
        "search": search or None,
        "panel": None,
        "segment": None,
    }


def _action_playbook(segment: str) -> dict:
    entry = ENTRY_BY_ID["retention_playbook"]
    params: dict[str, str] = {}
    if segment != "customers_all":
        params["segment"] = segment
    return {
        "action_id": "retention_playbook_panel",
        "label": "Show retention playbook in copilot",
        "action_type": "open_panel",
        "path": entry.path,
        "search": urlencode(params) if params else None,
        "panel": "retention_playbook",
        "segment": segment,
    }


def answer_question(
    conn: sqlite3.Connection,
    *,
    message: str,
    segment: str | None = None,
) -> dict:
    text = (message or "").strip()
    seg = normalize_segment(segment)
    if not text:
        return {
            "answer": "Ask about the book, customers, products, engagement, or admin — "
            "for example: “Show high churn customers” or “Open the product heatmap”.",
            "actions": [
                _action_navigate(ENTRY_BY_ID["business"], segment=seg),
                _action_navigate(ENTRY_BY_ID["products"]),
                _action_navigate(ENTRY_BY_ID["customer_churn"]),
            ],
            "citations": [],
        }

    lowered = text.lower()
    actions: list[dict] = []
    snippets: list[str] = []

    overview = _overview_snippet(conn)
    if overview and any(w in lowered for w in ("how many", "count", "customers", "book size")):
        snippets.append(overview)

    if any(
        w in lowered
        for w in ("kpi", "retention", "book value", "churn risk", "portfolio", "value at risk")
    ):
        port = _portfolio_snippet(conn, seg)
        if port:
            snippets.append(port)

    entry = _pick_entry(lowered)
    if entry is None:
        answer = (
            "I can open areas of Customer 360 and suggest filtered views. "
            "Try naming a workspace (business, customer, products, engagement, admin) "
            "or ask for high churn customers or the retention playbook."
        )
        if snippets:
            answer = " ".join(snippets) + " " + answer
        actions = [
            _action_navigate(ENTRY_BY_ID["business"], segment=seg),
            _action_navigate(ENTRY_BY_ID["customer"]),
            _action_navigate(ENTRY_BY_ID["products"]),
        ]
        return {"answer": answer, "actions": actions, "citations": ["app_catalog"]}

    if entry.entry_id == "retention_playbook" or (
        "playbook" in lowered and "retention" in lowered
    ):
        answer = (
            "The retention playbook lists at-risk customers for your cohort with suggested actions. "
            "Open it here in the copilot or go to The business for full KPI context."
        )
        if snippets:
            answer = " ".join(snippets) + " " + answer
        actions = [
            _action_playbook(seg),
            _action_navigate(ENTRY_BY_ID["business"], segment=seg),
            _action_navigate(ENTRY_BY_ID["customer_churn"]),
        ]
        return {"answer": answer, "actions": actions, "citations": ["retention_playbook"]}

    answer = f"{entry.description}"
    if snippets:
        answer = " ".join(snippets) + " " + answer
    else:
        answer = answer + " Use the link below to open that view (the copilot stays open)."

    actions.append(_action_navigate(entry, segment=seg if entry.path == "/business" else None))

    if entry.entry_id == "business":
        actions.append(_action_playbook(seg))
    elif entry.entry_id == "customer_churn":
        actions.append(_action_navigate(ENTRY_BY_ID["customer"], segment=seg))

    return {
        "answer": answer,
        "actions": actions[:4],
        "citations": [entry.entry_id],
    }
