"""Validated dashboard actions the assistant can offer (Insurance-style chips)."""

from __future__ import annotations

from typing import Any


def action_metric_filter(filter_id: str, *, label: str) -> dict[str, Any]:
    return {
        "action_id": f"metric_{filter_id}",
        "label": label,
        "action_type": "metric_filter",
        "payload": {"filter_id": filter_id},
    }


def action_focus_panel(panel_id: str, *, label: str) -> dict[str, Any]:
    return {
        "action_id": f"panel_{panel_id}",
        "label": label,
        "action_type": "focus_panel",
        "payload": {"panel_id": panel_id},
    }


def action_filter_controls(
    *,
    label: str,
    domain: str | None = None,
    golden_only: bool | None = None,
    similarity_key: str | None = None,
    risk_tier: str | None = None,
    needs_attention: bool | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if domain:
        payload["domain"] = domain
    if golden_only is not None:
        payload["golden_only"] = golden_only
    if similarity_key:
        payload["similarity_key"] = similarity_key
    if risk_tier:
        payload["risk_tier"] = risk_tier
    if needs_attention is not None:
        payload["needs_attention"] = needs_attention
    if search:
        payload["search"] = search
    return {
        "action_id": "filter_controls",
        "label": label,
        "action_type": "filter_controls",
        "payload": payload,
    }


def action_filter_alerts(
    *,
    label: str,
    status: str | None = None,
    min_risk: float | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if status:
        payload["status"] = status
    if min_risk is not None:
        payload["min_risk"] = min_risk
    return {
        "action_id": "filter_alerts",
        "label": label,
        "action_type": "filter_alerts",
        "payload": payload,
    }


def action_open_detail(kind: str, entity_id: int, *, label: str) -> dict[str, Any]:
    return {
        "action_id": f"detail_{kind}_{entity_id}",
        "label": label,
        "action_type": "open_detail",
        "payload": {"kind": kind, "id": entity_id},
    }


def action_open_control_code(control_code: str, control_id: int, *, label: str | None = None) -> dict[str, Any]:
    return {
        "action_id": f"control_{control_code}",
        "label": label or f"Open {control_code}",
        "action_type": "open_detail",
        "payload": {"kind": "controls", "id": control_id},
    }
