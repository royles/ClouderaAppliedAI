"""Product catalog summary for heatmap navigation."""

from __future__ import annotations

from typing import Any

from customer360.agent.tools.context import ToolContext
from customer360.agent.tools.registry import register_tool
from customer360.api.product_catalog import fetch_product_catalog


@register_tool(
    "get_product_catalog_summary",
    description="Policy products grouped by class with customer counts (for heatmap / product drill-down).",
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
)
def get_product_catalog_summary(ctx: ToolContext, _input: dict[str, Any]) -> dict[str, Any]:
    catalog = fetch_product_catalog(ctx.conn)
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
    return {
        "max_customer_count": catalog.get("max_customer_count", 0),
        "top_products": top[:12],
        "navigation": {"path": "/products", "catalog_entry_id": "products"},
    }
