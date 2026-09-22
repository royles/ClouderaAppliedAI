"""Async retention queue recommendations — LLM-generated per customer profile."""

from __future__ import annotations

import sqlite3

from customer360.api.retention_queue_llm import generate_retention_recommendations_llm


def fetch_retention_recommendations(
    conn: sqlite3.Connection,
    customer_ids: list[int],
    *,
    locale: str | None = None,
) -> dict:
    recommendations, llm_configured = generate_retention_recommendations_llm(
        conn,
        customer_ids,
        locale=locale,
    )
    return {
        "recommendations": recommendations,
        "llm_configured": llm_configured,
    }
