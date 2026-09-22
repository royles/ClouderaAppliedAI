"""Portfolio KPIs for a cohort segment."""

from __future__ import annotations

from typing import Any

from customer360.agent.kpi_benchmark_context import benchmark_assessments_for_targets
from customer360.agent.tools.context import ToolContext
from customer360.agent.tools.registry import register_tool
from customer360.api.portfolio_analytics import fetch_portfolio_analytics
from customer360.api.segments import normalize_segment


@register_tool(
    "get_portfolio_kpis",
    description=(
        "Portfolio KPIs (book value, retention forecast, value at churn risk) for a business segment, "
        "including vs admin benchmark targets (green/amber/red)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "segment": {
                "type": "string",
                "description": "Overview segment key, e.g. customers_all, with_policies",
            },
        },
        "additionalProperties": False,
    },
)
def get_portfolio_kpis(ctx: ToolContext, tool_input: dict[str, Any]) -> dict[str, Any]:
    seg = normalize_segment(tool_input.get("segment") or ctx.segment)
    payload = fetch_portfolio_analytics(ctx.conn, segment=seg)
    kpis = payload.get("kpis") or {}
    kpi_targets = payload.get("kpi_targets") or {}
    benchmark_assessments = benchmark_assessments_for_targets(ctx.conn, kpi_targets)
    return {
        "segment": seg,
        "kpis": {
            k: kpis.get(k)
            for k in (
                "total_book_value",
                "avg_customer_value",
                "annual_retention_rate_forecast",
                "value_at_risk_12m",
                "weighted_churn_probability",
                "high_risk_customers",
                "active_customers",
                "book_growth_pct",
            )
        },
        "benchmark_assessments": benchmark_assessments,
    }
