"""Catalog and filter vocabulary for navigation questions."""

from __future__ import annotations

from typing import Any

from customer360.agent.catalog import CATALOG
from customer360.agent.tools.context import ToolContext
from customer360.agent.tools.registry import register_tool
from customer360.api.customer_list import KNOWN_CITIES
from customer360.api.segments import OVERVIEW_DOMAINS, SEGMENT_WHERE


@register_tool(
    "list_app_navigation_catalog",
    description="Major app areas the copilot can open (ids, titles, paths, and phrase hints).",
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
)
def list_app_navigation_catalog(_ctx: ToolContext, _input: dict[str, Any]) -> dict[str, Any]:
    entries = [
        {
            "catalog_entry_id": e.entry_id,
            "title": e.title,
            "path": e.path,
            "default_search": e.search or None,
            "phrase_hints": list(e.phrases),
        }
        for e in CATALOG
    ]
    return {"entries": entries}


@register_tool(
    "list_overview_segments",
    description="Valid overview / cohort segment keys with human labels (for filters and KPIs).",
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
)
def list_overview_segments(_ctx: ToolContext, _input: dict[str, Any]) -> dict[str, Any]:
    segments = [
        {"segment_key": key, "label": label, "description": desc}
        for label, key, desc, _sql in OVERVIEW_DOMAINS
    ]
    return {"segments": segments, "valid_keys": sorted(SEGMENT_WHERE.keys())}


@register_tool(
    "list_known_cities",
    description="City names recognized for customer list city filters (Israeli seed data).",
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
)
def list_known_cities(_ctx: ToolContext, _input: dict[str, Any]) -> dict[str, Any]:
    canonical = sorted(set(KNOWN_CITIES.values()))
    return {"cities": canonical}
