"""Compare portfolio KPIs across two overview cohort segments."""

from __future__ import annotations

from typing import Any

from customer360.agent.tools.context import ToolContext
from customer360.agent.tools.registry import register_tool
from customer360.api.portfolio_analytics import fetch_portfolio_analytics
from customer360.api.segments import SEGMENT_WHERE, normalize_segment

_KPI_KEYS = (
    "active_customers",
    "total_book_value",
    "avg_customer_value",
    "annual_retention_rate_forecast",
    "value_at_risk_12m",
    "weighted_churn_probability",
    "high_risk_customers",
)


def _segment_kpis(conn, segment: str) -> dict[str, Any]:
    payload = fetch_portfolio_analytics(conn, segment=segment)
    kpis = payload.get("kpis") or {}
    return {k: kpis.get(k) for k in _KPI_KEYS}


@register_tool(
    "compare_portfolio_segments",
    description=(
        "Side-by-side portfolio KPIs for two cohort segments (e.g. customers_all vs with_policies)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "segment_a": {
                "type": "string",
                "description": f"First segment; one of: {', '.join(sorted(SEGMENT_WHERE))}",
            },
            "segment_b": {
                "type": "string",
                "description": "Second segment key",
            },
        },
        "required": ["segment_a", "segment_b"],
        "additionalProperties": False,
    },
)
def compare_portfolio_segments(ctx: ToolContext, tool_input: dict[str, Any]) -> dict[str, Any]:
    seg_a = normalize_segment(tool_input.get("segment_a"))
    seg_b = normalize_segment(tool_input.get("segment_b"))
    kpis_a = _segment_kpis(ctx.conn, seg_a)
    kpis_b = _segment_kpis(ctx.conn, seg_b)
    deltas: dict[str, Any] = {}
    for key in _KPI_KEYS:
        a = kpis_a.get(key)
        b = kpis_b.get(key)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            deltas[key] = round(float(b) - float(a), 4)
        else:
            deltas[key] = None
    return {
        "segment_a": {"key": seg_a, "kpis": kpis_a},
        "segment_b": {"key": seg_b, "kpis": kpis_b},
        "delta_b_minus_a": deltas,
    }
