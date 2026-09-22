"""Data freshness timestamps for the executive copilot."""

from __future__ import annotations

from typing import Any

from customer360.agent.tools.context import ToolContext
from customer360.agent.tools.registry import register_tool
from customer360.api.data_freshness import fetch_data_freshness


@register_tool(
    "get_data_freshness",
    description=(
        "When warehouse loads, customer metrics, portfolio cache, and churn scores were last refreshed."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
)
def get_data_freshness(ctx: ToolContext, _input: dict[str, Any]) -> dict[str, Any]:
    payload = fetch_data_freshness(ctx.conn)
    return {
        "warehouse_loaded_at": payload.get("warehouse_loaded_at"),
        "customer_metrics_at": payload.get("customer_metrics_at"),
        "portfolio_cache_at": payload.get("portfolio_cache_at"),
        "churn_scored_at": payload.get("churn_scored_at"),
        "churn_customer_count": payload.get("churn_customer_count"),
    }
