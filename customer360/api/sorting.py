"""Customer list sort options."""

from __future__ import annotations

from typing import Literal

SortBy = Literal["name", "policy_count", "investment_count"]
SortOrder = Literal["asc", "desc"]

SORT_SQL: dict[str, str] = {
    "name": "c.CUSTOMER_NAME",
    "policy_count": "policy_count",
    "investment_count": "investment_count",
}


def normalize_sort_by(value: str | None) -> str:
    key = (value or "name").strip().lower()
    return key if key in SORT_SQL else "name"


def normalize_sort_order(value: str | None, *, sort_by: str) -> str:
    order = (value or "").strip().lower()
    if order in ("asc", "desc"):
        return order
    # Default: descending for numeric ranks, ascending for name
    return "desc" if sort_by in ("policy_count", "investment_count") else "asc"


def order_clause(sort_by: str, sort_order: str) -> str:
    column = SORT_SQL[sort_by]
    direction = "DESC" if sort_order == "desc" else "ASC"
    if sort_by == "name":
        return f"{column} {direction}, c.CUSTOMER_ID ASC"
    return f"{column} {direction}, c.CUSTOMER_NAME ASC"
