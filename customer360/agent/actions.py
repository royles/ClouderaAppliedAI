"""Validated navigation actions derived from the app catalog."""

from __future__ import annotations

from urllib.parse import urlencode

from customer360.agent.catalog import CATALOG, CatalogEntry, ENTRY_BY_ID
from customer360.agent.list_filters import (
    CustomerListFilters,
    action_label,
    to_query_string,
)

ALLOWED_ACTION_IDS = frozenset(e.entry_id for e in CATALOG)

CUSTOMER_ENTRY_IDS = frozenset({"customer", "customer_churn", "customer_top_value"})


def _parse_entry_search(search: str) -> dict[str, str]:
    params: dict[str, str] = {}
    if not search:
        return params
    for part in search.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            params[k] = v
    return params


def _search_from_entry(entry: CatalogEntry, *, segment: str | None) -> str:
    params = _parse_entry_search(entry.search)
    if segment and entry.entry_id in ("business", "retention_playbook"):
        if segment != "customers_all":
            params["segment"] = segment
    return urlencode(params)


def action_navigate(
    entry: CatalogEntry,
    *,
    segment: str | None = None,
    list_filters: CustomerListFilters | None = None,
    default_segment: str = "customers_all",
    label: str | None = None,
) -> dict:
    if entry.path == "/customer" and list_filters is not None:
        search = to_query_string(list_filters, default_segment=default_segment)
        action_label_text = label or action_label(list_filters.normalized(default_segment=default_segment))
    else:
        search = _search_from_entry(entry, segment=segment)
        action_label_text = label or f"Open {entry.title}"

    return {
        "action_id": entry.entry_id,
        "label": action_label_text,
        "action_type": "navigate",
        "path": entry.path,
        "search": search or None,
        "panel": None,
        "segment": None,
    }


def action_playbook(segment: str) -> dict:
    entry = ENTRY_BY_ID["retention_playbook"]
    params: dict[str, str] = {}
    if segment != "customers_all":
        params["segment"] = segment
    return {
        "action_id": "retention_playbook_panel",
        "label": "Show retention playbook in assistant",
        "action_type": "open_panel",
        "path": entry.path,
        "search": urlencode(params) if params else None,
        "panel": "retention_playbook",
        "segment": segment,
    }


def action_customer_list(
    list_filters: CustomerListFilters,
    *,
    default_segment: str,
    entry_id: str = "customer",
) -> dict:
    entry = ENTRY_BY_ID.get(entry_id) or ENTRY_BY_ID["customer"]
    f = list_filters.normalized(default_segment=default_segment)
    return action_navigate(
        entry,
        list_filters=f,
        default_segment=default_segment,
        label=action_label(f),
    )


def actions_from_model_ids(
    action_ids: list[str],
    *,
    segment: str,
    open_retention_playbook: bool,
    list_filters: CustomerListFilters | None = None,
) -> list[dict]:
    actions: list[dict] = []
    seen: set[str] = set()

    if open_retention_playbook and "retention_playbook_panel" not in seen:
        actions.append(action_playbook(segment))
        seen.add("retention_playbook_panel")

    if list_filters and not action_ids:
        actions.append(
            action_customer_list(list_filters, default_segment=segment),
        )
        return actions[:4]

    for raw_id in action_ids:
        entry_id = raw_id.strip()
        if entry_id not in ALLOWED_ACTION_IDS or entry_id in seen:
            continue
        entry = ENTRY_BY_ID[entry_id]
        if entry_id == "retention_playbook":
            actions.append(action_playbook(segment))
            seen.add("retention_playbook_panel")
            continue

        seg = segment if entry.path == "/business" else None
        filters = list_filters if entry.path == "/customer" else None
        actions.append(
            action_navigate(
                entry,
                segment=seg,
                list_filters=filters,
                default_segment=segment,
            ),
        )
        seen.add(entry_id)
        if len(actions) >= 4:
            break

    if list_filters and not any(a.get("path") == "/customer" for a in actions):
        actions.insert(
            0,
            action_customer_list(list_filters, default_segment=segment),
        )

    return actions[:4]
