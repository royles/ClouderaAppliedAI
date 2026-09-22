"""Validated navigation actions derived from the app catalog."""

from __future__ import annotations

from urllib.parse import urlencode

from customer360.agent.catalog import CATALOG, CatalogEntry, ENTRY_BY_ID

ALLOWED_ACTION_IDS = frozenset(e.entry_id for e in CATALOG)


def action_navigate(entry: CatalogEntry, *, segment: str | None = None) -> dict:
    search = entry.search
    if segment and entry.entry_id in ("business", "retention_playbook"):
        params: dict[str, str] = {}
        if entry.search:
            for part in entry.search.split("&"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    params[k] = v
        if segment != "customers_all":
            params["segment"] = segment
        search = urlencode(params)
    return {
        "action_id": entry.entry_id,
        "label": f"Open {entry.title}",
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
        "label": "Show retention playbook in copilot",
        "action_type": "open_panel",
        "path": entry.path,
        "search": urlencode(params) if params else None,
        "panel": "retention_playbook",
        "segment": segment,
    }


def actions_from_model_ids(
    action_ids: list[str],
    *,
    segment: str,
    open_retention_playbook: bool,
) -> list[dict]:
    actions: list[dict] = []
    seen: set[str] = set()

    if open_retention_playbook and "retention_playbook_panel" not in seen:
        actions.append(action_playbook(segment))
        seen.add("retention_playbook_panel")

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
        actions.append(action_navigate(entry, segment=seg))
        seen.add(entry_id)
        if len(actions) >= 4:
            break
    return actions
