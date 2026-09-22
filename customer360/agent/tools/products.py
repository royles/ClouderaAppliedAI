"""Product catalog summary for heatmap navigation."""

from __future__ import annotations

from typing import Any

from customer360.agent.tools.context import ToolContext
from customer360.agent.tools.registry import register_tool
from customer360.api.product_catalog import fetch_product_catalog


@register_tool(
    "get_product_catalog_summary",
    description="Policy products grouped by class with customer counts (for heatmap / product drill-down).",
    input_schema={
        "type": "object",
        "properties": {
            "segment": {"type": "string"},
            "city": {"type": "string"},
        },
        "additionalProperties": False,
    },
)
def get_product_catalog_summary(ctx: ToolContext, tool_input: dict[str, Any]) -> dict[str, Any]:
    catalog = fetch_product_catalog(
        ctx.conn,
        segment=tool_input.get("segment") or ctx.segment,
        city=tool_input.get("city"),
    )
    top: list[dict[str, Any]] = []
    for group in catalog.get("classes", []):
        for product in group.get("products", []):
            top.append(
                {
                    "policy_type_code": product["policy_type_code"],
                    "policy_type_desc": product["policy_type_desc"],
                    "customer_count": product["customer_count"],
                    "class_label": group["class_label"],
                }
            )
    top.sort(key=lambda p: p["customer_count"], reverse=True)
    filters = catalog.get("filters") or {}
    nav_search = ""
    seg = filters.get("segment")
    if seg and seg != "customers_all":
        nav_search += f"segment={seg}"
    city = filters.get("city")
    if city:
        nav_search += ("&" if nav_search else "") + f"city={city}"
    return {
        "max_customer_count": catalog.get("max_customer_count", 0),
        "filters": filters,
        "top_products": top[:12],
        "navigation": {
            "path": "/products",
            "search": nav_search or None,
            "catalog_entry_id": "products",
        },
    }
