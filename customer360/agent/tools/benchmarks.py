"""KPI benchmark targets configured in Data & admin."""

from __future__ import annotations

from typing import Any

from customer360.agent.tools.context import ToolContext
from customer360.agent.tools.registry import register_tool
from customer360.kpi_benchmarks import benchmark_for_api, list_kpi_benchmarks


@register_tool(
    "get_kpi_benchmarks",
    description="Executive KPI targets and amber thresholds from the admin benchmark catalog.",
    input_schema={
        "type": "object",
        "properties": {
            "enabled_only": {"type": "boolean", "description": "Omit disabled benchmarks when true"},
        },
        "additionalProperties": False,
    },
)
def get_kpi_benchmarks(ctx: ToolContext, tool_input: dict[str, Any]) -> dict[str, Any]:
    rows = list_kpi_benchmarks(ctx.conn, ensure_catalog=True)
    enabled_only = bool(tool_input.get("enabled_only", True))
    benchmarks = []
    for row in rows:
        item = benchmark_for_api(row)
        if enabled_only and not item.get("enabled"):
            continue
        benchmarks.append(
            {
                "kpi_key": item["kpi_key"],
                "display_label": item["display_label"],
                "target_value": item["target_value"],
                "amber_threshold": item["amber_threshold"],
                "direction": item["direction"],
                "unit_kind": item["unit_kind"],
            }
        )
    return {"benchmarks": benchmarks, "count": len(benchmarks)}
