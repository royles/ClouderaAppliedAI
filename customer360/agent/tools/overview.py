"""Overview domain card counts."""

from __future__ import annotations

from typing import Any

from customer360.agent.tools.context import ToolContext
from customer360.agent.tools.registry import register_tool
from customer360.api.segments import OVERVIEW_DOMAINS


@register_tool(
    "get_overview_counts",
    description="Current customer counts per overview domain card (customers, policies, foreclosures, etc.).",
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
)
def get_overview_counts(ctx: ToolContext, _input: dict[str, Any]) -> dict[str, Any]:
    conn = ctx.conn
    cache_ready = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_OVERVIEW_COUNTS'"
    ).fetchone()
    rows: list[dict[str, Any]] = []
    for label, filter_key, description, count_sql in OVERVIEW_DOMAINS:
        if cache_ready:
            row = conn.execute(
                "SELECT ROW_COUNT FROM APP_OVERVIEW_COUNTS WHERE FILTER_KEY = ?",
                (filter_key,),
            ).fetchone()
            count = int(row[0]) if row else int(conn.execute(count_sql).fetchone()[0])
        else:
            count = int(conn.execute(count_sql).fetchone()[0])
        rows.append(
            {
                "domain": label,
                "filter_key": filter_key,
                "description": description,
                "row_count": count,
            }
        )
    return {"domains": rows}
