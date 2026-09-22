"""Retention playbook queue for at-risk customers."""

from __future__ import annotations

from typing import Any

from customer360.agent.tools.context import ToolContext
from customer360.agent.tools.registry import register_tool
from customer360.api.retention_playbook import fetch_retention_playbook
from customer360.api.segments import normalize_segment


@register_tool(
    "get_retention_playbook_preview",
    description=(
        "Top customers by value-at-churn-risk with recommended retention actions for a cohort segment."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "segment": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 15},
        },
        "additionalProperties": False,
    },
)
def get_retention_playbook_preview(ctx: ToolContext, tool_input: dict[str, Any]) -> dict[str, Any]:
    seg = normalize_segment(tool_input.get("segment") or ctx.segment)
    try:
        limit = int(tool_input.get("limit", 8))
    except (TypeError, ValueError):
        limit = 8
    limit = max(1, min(limit, 15))
    data = fetch_retention_playbook(ctx.conn, segment=seg, limit=limit, offset=0)
    items = []
    for row in data.get("items") or []:
        action = row.get("recommended_action") or {}
        items.append(
            {
                "customer_name": row.get("customer_name"),
                "city_name": row.get("city_name"),
                "customer_value": row.get("customer_value"),
                "churn_risk_tier": row.get("churn_risk_tier"),
                "value_at_risk": row.get("value_at_risk"),
                "recommended_action_title": action.get("title"),
            }
        )
    return {
        "segment": seg,
        "total_in_queue": data.get("total", 0),
        "preview": items,
        "navigation": {"catalog_entry_id": "retention_playbook", "path": "/business"},
    }
