"""Customer list sort options."""

from __future__ import annotations

from typing import Literal

SortBy = Literal["name", "policy_count", "investment_count", "churn_risk"]
SortOrder = Literal["asc", "desc"]

SORT_SQL: dict[str, str] = {
    "name": "c.CUSTOMER_NAME",
    "policy_count": "policy_count",
    "investment_count": "investment_count",
}

DEFAULT_SORT_BY = "churn_risk"


def normalize_sort_by(value: str | None) -> str:
    key = (value or DEFAULT_SORT_BY).strip().lower()
    if key in ("churn", "churn_probability", "churn_risk_tier"):
        key = "churn_risk"
    if key == "churn_risk":
        return key
    return key if key in SORT_SQL else DEFAULT_SORT_BY


def normalize_sort_order(value: str | None, *, sort_by: str) -> str:
    order = (value or "").strip().lower()
    if order in ("asc", "desc"):
        return order
    if sort_by == "churn_risk":
        return "desc"
    return "desc" if sort_by in ("policy_count", "investment_count") else "asc"


def order_clause(sort_by: str, sort_order: str) -> str:
    if sort_by == "churn_risk":
        if sort_order == "desc":
            return (
                "CASE ch.CHURN_RISK_TIER "
                "WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 3 ELSE 4 END ASC, "
                "ch.CHURN_PROBABILITY DESC, c.CUSTOMER_NAME ASC"
            )
        return (
            "CASE ch.CHURN_RISK_TIER "
            "WHEN 'LOW' THEN 1 WHEN 'MEDIUM' THEN 2 WHEN 'HIGH' THEN 3 ELSE 4 END ASC, "
            "ch.CHURN_PROBABILITY ASC, c.CUSTOMER_NAME ASC"
        )
    column = SORT_SQL[sort_by]
    direction = "DESC" if sort_order == "desc" else "ASC"
    if sort_by == "name":
        return f"{column} {direction}, c.CUSTOMER_ID ASC"
    return f"{column} {direction}, c.CUSTOMER_NAME ASC"
