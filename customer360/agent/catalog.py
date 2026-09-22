"""Static app catalog: pages, deep links, and phrase hints for the rule router."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogEntry:
    entry_id: str
    title: str
    description: str
    path: str
    search: str = ""
    phrases: tuple[str, ...] = ()


CATALOG: tuple[CatalogEntry, ...] = (
    CatalogEntry(
        "business",
        "The business",
        "Portfolio KPIs, cohort filters, charts, and cohort comparison.",
        "/business",
        phrases=("business", "portfolio", "book", "kpis", "overview", "cohort", "dashboard"),
    ),
    CatalogEntry(
        "customer",
        "The customer",
        "Customer 360 list, profiles, value, churn, and insights.",
        "/customer",
        phrases=("customer", "customers", "360", "profile", "list"),
    ),
    CatalogEntry(
        "customer_churn",
        "High churn customers",
        "Customer list sorted by churn risk (highest first).",
        "/customer",
        "sort=churn_risk&order=desc",
        phrases=("high churn", "churn risk", "at risk customers", "lapse"),
    ),
    CatalogEntry(
        "products",
        "Products",
        "Product heatmap by class; drill down to customers per product.",
        "/products",
        phrases=("product", "products", "heatmap", "policy type"),
    ),
    CatalogEntry(
        "engagement",
        "Engagement",
        "Touchpoints, influence priority, and next best actions.",
        "/engagement",
        phrases=("engagement", "touchpoint", "next best", "outreach"),
    ),
    CatalogEntry(
        "admin",
        "Data & admin",
        "Warehouse health, schema map, data source, and KPI benchmarks.",
        "/admin",
        phrases=("admin", "warehouse", "schema", "data quality", "health"),
    ),
    CatalogEntry(
        "retention_playbook",
        "Retention playbook",
        "Prioritized at-risk customers with recommended actions for the active cohort.",
        "/business",
        "",
        phrases=("retention playbook", "playbook", "value at churn", "churn risk queue"),
    ),
)

ENTRY_BY_ID = {e.entry_id: e for e in CATALOG}
