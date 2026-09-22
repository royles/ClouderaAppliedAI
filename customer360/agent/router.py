"""Rule-based intent routing (fallback when Bedrock is unavailable)."""

from __future__ import annotations

import re
import sqlite3

from customer360.agent.actions import action_customer_list, action_navigate, action_playbook
from customer360.agent.catalog import CATALOG, CatalogEntry, ENTRY_BY_ID
from customer360.agent.context import gather_context
from customer360.agent.list_filters import CustomerListFilters
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


def _join_snippets(snippets: list[str]) -> str:
    return " ".join(s for s in snippets if s)


def answer_question_rules(
    conn: sqlite3.Connection,
    *,
    message: str,
    segment: str | None = None,
    merged_list: CustomerListFilters | None = None,
    extra_snippets: list[str] | None = None,
) -> dict:
    text = (message or "").strip()
    seg = normalize_segment(segment)
    if not text:
        return {
            "answer": "Ask about the book, customers, products, engagement, or admin — "
            "for example: “Show high churn customers” or “Open the product heatmap”.",
            "actions": [
                action_navigate(ENTRY_BY_ID["business"], segment=seg, default_segment=seg),
                action_navigate(ENTRY_BY_ID["products"], default_segment=seg),
                action_navigate(ENTRY_BY_ID["customer_churn"], default_segment=seg),
            ],
            "citations": [],
        }

    lowered = text.lower()
    ctx = gather_context(conn, message=text, segment=seg)
    snippets = list(extra_snippets or ctx["snippets"])

    if merged_list:
        fl = merged_list
        entry_id = (
            "customer_top_value"
            if fl.sort_by == "customer_value"
            else "customer_churn"
            if fl.sort_by == "churn_risk"
            else "customer"
        )
        parts = [
            f"sorted by {fl.sort_by.replace('_', ' ')} ({fl.sort_order})",
            f"{fl.page_size} per page",
        ]
        if fl.city:
            parts.insert(0, f"city = {fl.city}")
        answer = "Opening the customer list: " + ", ".join(parts) + "."
        if snippets:
            answer = _join_snippets(snippets) + " " + answer
        return {
            "answer": answer,
            "actions": [
                action_customer_list(
                    fl,
                    default_segment=seg,
                    entry_id=entry_id,
                ),
            ],
            "citations": ["customer_list", entry_id],
        }

    entry = _pick_entry(lowered)
    if entry is None:
        answer = (
            "I can open areas of Customer 360 and suggest filtered views. "
            "Try naming a workspace (business, customer, products, engagement, admin) "
            "or ask for high churn customers or the retention playbook."
        )
        if snippets:
            answer = _join_snippets(snippets) + " " + answer
        actions = [
            action_navigate(ENTRY_BY_ID["business"], segment=seg, default_segment=seg),
            action_navigate(ENTRY_BY_ID["customer"], default_segment=seg),
            action_navigate(ENTRY_BY_ID["products"], default_segment=seg),
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
            answer = _join_snippets(snippets) + " " + answer
        actions = [
            action_playbook(seg),
            action_navigate(ENTRY_BY_ID["business"], segment=seg, default_segment=seg),
            action_navigate(
                ENTRY_BY_ID["customer_churn"],
                default_segment=seg,
                list_filters=CustomerListFilters(
                    sort_by="churn_risk",
                    sort_order="desc",
                    page_size=25,
                    view="table",
                ),
            ),
        ]
        return {"answer": answer, "actions": actions, "citations": ["retention_playbook"]}

    answer = f"{entry.description}"
    if snippets:
        answer = _join_snippets(snippets) + " " + answer
    else:
        answer = answer + " Use the link below to open that view (the copilot stays open)."

    actions: list[dict] = []
    list_filters = None
    if entry.path == "/customer" and entry.search:
        list_filters = CustomerListFilters(
            sort_by="churn_risk" if entry.entry_id == "customer_churn" else "customer_value",
            sort_order="desc",
            page_size=25,
            view="table",
        )

    actions.append(
        action_navigate(
            entry,
            segment=seg if entry.path == "/business" else None,
            list_filters=list_filters,
            default_segment=seg,
        ),
    )

    if entry.entry_id == "business":
        actions.append(action_playbook(seg))
    elif entry.entry_id == "customer_churn":
        actions.append(
            action_navigate(ENTRY_BY_ID["customer"], default_segment=seg, list_filters=list_filters),
        )

    return {
        "answer": answer,
        "actions": actions[:4],
        "citations": [entry.entry_id],
    }
