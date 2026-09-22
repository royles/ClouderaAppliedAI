"""Customer search, counts, and list navigation (parameterized SQL only)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from customer360.agent.actions import action_customer_list, action_navigate
from customer360.agent.catalog import ENTRY_BY_ID
from customer360.agent.customer_snippet import top_customers_snippet
from customer360.agent.list_filters import (
    CustomerListFilters,
    clamp_page_size,
    merge_filters,
    filters_from_list_context,
)
from customer360.agent.query_builder import count_matching_customers
from customer360.agent.tools.context import ToolContext
from customer360.agent.tools.registry import register_tool
from customer360.api.customer_list import customer_list_where, normalize_city_name
from customer360.api.segments import normalize_segment


def _filters_from_tool_input(ctx: ToolContext, tool_input: dict[str, Any]) -> CustomerListFilters:
    prior = filters_from_list_context(ctx.list_context)
    seg = tool_input.get("segment")
    page_size_raw = tool_input.get("limit") or tool_input.get("page_size")
    try:
        page_size = clamp_page_size(int(page_size_raw)) if page_size_raw is not None else 50
    except (TypeError, ValueError):
        page_size = 50
    sort_by = str(tool_input.get("sort_by") or "churn_risk").strip().lower()
    if sort_by in ("value", "customer_value"):
        sort_by = "customer_value"
    sort_order = str(tool_input.get("sort_order") or "desc").strip().lower()
    if sort_order not in ("asc", "desc"):
        sort_order = "desc"
    city = normalize_city_name(tool_input.get("city"))
    view = tool_input.get("view")
    patch = CustomerListFilters(
        segment=normalize_segment(seg) if seg else None,
        sort_by=sort_by,
        sort_order=sort_order,
        page_size=page_size,
        page=1,
        view="table" if view == "table" or (page_size <= 25) else None,
        city=city,
    )
    merged = merge_filters(prior, patch, default_segment=ctx.segment)
    if merged is None:
        merged = patch.normalized(default_segment=ctx.segment)
    return merged


@register_tool(
    "count_customers",
    description="Count customers matching list filters (same rules as the customer directory API).",
    input_schema={
        "type": "object",
        "properties": {
            "segment": {"type": "string"},
            "city": {"type": "string", "description": "e.g. Jerusalem, Tel Aviv"},
            "sort_by": {
                "type": "string",
                "enum": ["customer_value", "churn_risk", "name", "policy_count", "investment_count"],
            },
        },
        "additionalProperties": False,
    },
)
def count_customers(ctx: ToolContext, tool_input: dict[str, Any]) -> dict[str, Any]:
    filters = _filters_from_tool_input(ctx, tool_input)
    total = count_matching_customers(ctx.conn, filters, default_segment=ctx.segment)
    return {
        "count": total,
        "filters": asdict(filters.normalized(default_segment=ctx.segment)),
    }


@register_tool(
    "preview_customer_ranking",
    description="Top N customers by sort order with names and values (for executive summaries).",
    input_schema={
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "minimum": 1, "maximum": 25},
            "sort_by": {
                "type": "string",
                "enum": ["customer_value", "churn_risk", "name", "policy_count", "investment_count"],
            },
            "sort_order": {"type": "string", "enum": ["asc", "desc"]},
            "city": {"type": "string"},
            "segment": {"type": "string"},
        },
        "required": ["limit", "sort_by"],
        "additionalProperties": False,
    },
)
def preview_customer_ranking(ctx: ToolContext, tool_input: dict[str, Any]) -> dict[str, Any]:
    tool_input = {**tool_input, "page_size": tool_input.get("limit", 10)}
    filters = _filters_from_tool_input(ctx, tool_input)
    limit = min(25, max(1, int(tool_input.get("limit", 10))))
    text = top_customers_snippet(
        ctx.conn,
        filters=filters,
        default_segment=ctx.segment,
        limit=limit,
    )
    return {
        "summary": text,
        "filters": asdict(filters.normalized(default_segment=ctx.segment)),
    }


@register_tool(
    "prepare_customer_list_link",
    description="Build a validated /customer URL and action for the UI from list filters.",
    input_schema={
        "type": "object",
        "properties": {
            "segment": {"type": "string"},
            "sort_by": {
                "type": "string",
                "enum": ["customer_value", "churn_risk", "name", "policy_count", "investment_count"],
            },
            "sort_order": {"type": "string", "enum": ["asc", "desc"]},
            "page_size": {"type": "integer", "minimum": 1, "maximum": 100},
            "city": {"type": "string"},
            "view": {"type": "string", "enum": ["grid", "table"]},
        },
        "additionalProperties": False,
    },
)
def prepare_customer_list_link(ctx: ToolContext, tool_input: dict[str, Any]) -> dict[str, Any]:
    filters = _filters_from_tool_input(ctx, tool_input)
    entry_id = (
        "customer_top_value"
        if filters.sort_by == "customer_value"
        else "customer_churn"
        if filters.sort_by == "churn_risk"
        else "customer"
    )
    action = action_customer_list(filters, default_segment=ctx.segment, entry_id=entry_id)
    return {
        "action": action,
        "customer_list": asdict(filters.normalized(default_segment=ctx.segment)),
    }


@register_tool(
    "suggest_app_navigation",
    description="Open a major app area by catalog id (business, customer, products, engagement, admin).",
    input_schema={
        "type": "object",
        "properties": {
            "catalog_entry_id": {
                "type": "string",
                "description": "e.g. business, customer, customer_top_value, products, engagement, admin",
            },
            "segment": {"type": "string", "description": "Business segment when opening /business"},
        },
        "required": ["catalog_entry_id"],
        "additionalProperties": False,
    },
)
@register_tool(
    "search_customers_by_name",
    description="Find customers by partial name or id within the active segment (for lookup before opening a profile).",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Substring of customer name or id"},
            "segment": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 15},
        },
        "required": ["query"],
        "additionalProperties": False,
    },
)
def search_customers_by_name(ctx: ToolContext, tool_input: dict[str, Any]) -> dict[str, Any]:
    q = str(tool_input.get("query", "")).strip()
    if len(q) < 2:
        return {"error": "query must be at least 2 characters", "matches": []}
    seg = normalize_segment(tool_input.get("segment") or ctx.segment)
    try:
        limit = int(tool_input.get("limit", 8))
    except (TypeError, ValueError):
        limit = 8
    limit = max(1, min(limit, 15))
    where, params = customer_list_where(seg, q)
    rows = ctx.conn.execute(
        f"""
        SELECT c.CUSTOMER_ID AS customer_id, c.CUSTOMER_NAME AS customer_name, c.CITY_NAME AS city_name
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        WHERE {where}
        ORDER BY c.CUSTOMER_NAME
        LIMIT ?
        """,
        [*params, limit],
    ).fetchall()
    total = ctx.conn.execute(
        f"SELECT COUNT(*) FROM DWH_DIM_CUSTOMERS_UNIQUE c WHERE {where}",
        params,
    ).fetchone()[0]
    matches = [
        {
            "customer_id": int(r["customer_id"]),
            "customer_name": r["customer_name"],
            "city_name": r["city_name"],
            "profile_path": f"/customer/{int(r['customer_id'])}",
        }
        for r in rows
    ]
    return {"segment": seg, "query": q, "total_matches": int(total or 0), "matches": matches}


def suggest_app_navigation(ctx: ToolContext, tool_input: dict[str, Any]) -> dict[str, Any]:
    entry_id = str(tool_input.get("catalog_entry_id", "")).strip()
    entry = ENTRY_BY_ID.get(entry_id)
    if entry is None:
        return {"error": f"Unknown catalog_entry_id: {entry_id}"}
    seg = normalize_segment(tool_input.get("segment") or ctx.segment)
    action = action_navigate(
        entry,
        segment=seg if entry.path == "/business" else None,
        default_segment=ctx.segment,
    )
    return {"action": action, "catalog_entry_id": entry_id}
