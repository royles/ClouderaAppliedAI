"""Engagement hub summaries and top outreach opportunities."""

from __future__ import annotations

from typing import Any

from customer360.agent.tools.context import ToolContext
from customer360.agent.tools.registry import register_tool
from customer360.api.engagement_hub import fetch_engagement_opportunities
from customer360.api.segments import normalize_segment


@register_tool(
    "get_engagement_summary",
    description=(
        "Book-wide touchpoint stats and top engagement opportunities (influence score) for a segment."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "segment": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 10},
        },
        "additionalProperties": False,
    },
)
def get_engagement_summary(ctx: ToolContext, tool_input: dict[str, Any]) -> dict[str, Any]:
    seg = normalize_segment(tool_input.get("segment") or ctx.segment)
    try:
        limit = int(tool_input.get("limit", 5))
    except (TypeError, ValueError):
        limit = 5
    limit = max(1, min(limit, 10))
    data = fetch_engagement_opportunities(ctx.conn, segment=seg, limit=limit, offset=0)
    top = []
    for row in data.get("opportunities") or []:
        rec = row.get("recommended_action") or {}
        top.append(
            {
                "customer_name": row.get("customer_name"),
                "city_name": row.get("city_name"),
                "customer_value": row.get("customer_value"),
                "influence_score": row.get("influence_score"),
                "next_step_title": rec.get("title"),
                "channel_hint": rec.get("channel_hint"),
            }
        )
    return {
        "segment": seg,
        "book_summary": data.get("book_summary") or {},
        "total_opportunities": data.get("total", 0),
        "top_opportunities": top,
        "navigation": {"catalog_entry_id": "engagement", "path": "/engagement"},
    }
