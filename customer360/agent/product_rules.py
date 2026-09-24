"""Rule-based answers for policy / product catalog questions."""

from __future__ import annotations

import sqlite3

from customer360.agent.actions import action_navigate
from customer360.agent.catalog import ENTRY_BY_ID
from customer360.agent.list_filters import is_policy_product_question
from customer360.api.product_catalog import fetch_product_catalog


def try_product_catalog_answer(
    conn: sqlite3.Connection,
    *,
    message: str,
    segment: str,
    extra_snippets: list[str] | None = None,
) -> dict | None:
    if not is_policy_product_question(message):
        return None

    catalog = fetch_product_catalog(conn, segment=segment)
    ranked: list[dict] = []
    for group in catalog.get("classes", []):
        for product in group.get("products", []):
            ranked.append(
                {
                    "policy_type_desc": str(
                        product.get("policy_type_desc") or product.get("policy_type_code")
                    ),
                    "customer_count": int(product.get("customer_count") or 0),
                    "class_label": str(group.get("class_label") or ""),
                }
            )
    ranked.sort(key=lambda p: p["customer_count"], reverse=True)
    if not ranked:
        return None

    best = ranked[0]
    runners = ranked[1:4]
    runner_text = ""
    if runners:
        runner_text = " Next: " + ", ".join(
            f"{p['policy_type_desc']} ({p['customer_count']:,})" for p in runners
        ) + "."

    answer = (
        f"In this demo, “best” is measured by customer adoption in the active cohort. "
        f"The leading product is {best['policy_type_desc']} "
        f"({best['customer_count']:,} customers, {best['class_label']}).{runner_text} "
        f"Open the product heatmap to compare classes and drill down by product."
    )

    if extra_snippets:
        prefix = " ".join(
            s
            for s in extra_snippets
            if s and not s.strip().lower().startswith("product catalog")
        ).strip()
        if prefix:
            answer = prefix + " " + answer

    return {
        "answer": answer,
        "actions": [
            action_navigate(ENTRY_BY_ID["products"], default_segment=segment),
            action_navigate(ENTRY_BY_ID["business"], segment=segment, default_segment=segment),
        ],
        "citations": ["products", "product_catalog"],
        "source": "local_catalog",
    }
