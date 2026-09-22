"""Rule-based intent routing (fallback when Bedrock is unavailable)."""

from __future__ import annotations

import re
import sqlite3

from customer360.agent.actions import action_navigate, action_playbook
from customer360.agent.catalog import CATALOG, CatalogEntry, ENTRY_BY_ID
from customer360.agent.context import gather_context
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


def answer_question_rules(
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
                action_navigate(ENTRY_BY_ID["business"], segment=seg),
                action_navigate(ENTRY_BY_ID["products"]),
                action_navigate(ENTRY_BY_ID["customer_churn"]),
            ],
            "citations": [],
        }

    lowered = text.lower()
    ctx = gather_context(conn, message=text, segment=seg)
    snippets = ctx["snippets"]

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
            action_navigate(ENTRY_BY_ID["business"], segment=seg),
            action_navigate(ENTRY_BY_ID["customer"]),
            action_navigate(ENTRY_BY_ID["products"]),
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
            action_playbook(seg),
            action_navigate(ENTRY_BY_ID["business"], segment=seg),
            action_navigate(ENTRY_BY_ID["customer_churn"]),
        ]
        return {"answer": answer, "actions": actions, "citations": ["retention_playbook"]}

    answer = f"{entry.description}"
    if snippets:
        answer = " ".join(snippets) + " " + answer
    else:
        answer = answer + " Use the link below to open that view (the copilot stays open)."

    actions: list[dict] = []
    actions.append(
        action_navigate(entry, segment=seg if entry.path == "/business" else None),
    )

    if entry.entry_id == "business":
        actions.append(action_playbook(seg))
    elif entry.entry_id == "customer_churn":
        actions.append(action_navigate(ENTRY_BY_ID["customer"], segment=seg))

    return {
        "answer": answer,
        "actions": actions[:4],
        "citations": [entry.entry_id],
    }
