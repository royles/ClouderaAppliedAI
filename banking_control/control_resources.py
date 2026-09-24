"""Evidence resource placeholders per control — link to documents when available."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from banking_control.control_workflows import WORKFLOW_TYPES, proposed_artifact_ref

RESOURCE_SLOT_DEFS: tuple[dict[str, str], ...] = (
    {
        "resource_key": "testing_workpaper",
        "label": "Control testing workpaper",
        "workflow_type": "testing_workpaper",
    },
    {
        "resource_key": "board_approval",
        "label": "Board / committee approval pack",
        "workflow_type": "board_approval",
    },
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slot_keys_for_control(description: str) -> list[dict[str, str]]:
    keys = [RESOURCE_SLOT_DEFS[0]]
    lower = (description or "").lower()
    if "board" in lower or "committee" in lower:
        keys.append(RESOURCE_SLOT_DEFS[1])
    return keys


def ensure_evidence_resources(conn: sqlite3.Connection, control_id: int, control_code: str, description: str) -> None:
    """Create placeholder rows for expected evidence slots (idempotent)."""
    now = _utc_now_iso()
    for slot in _slot_keys_for_control(description):
        wf_type = slot["workflow_type"]
        placeholder = proposed_artifact_ref(control_code, wf_type)
        existing = conn.execute(
            """
            SELECT resource_id FROM FCT_CONTROL_EVIDENCE_RESOURCE
            WHERE control_id = ? AND resource_key = ?
            """,
            (control_id, slot["resource_key"]),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE FCT_CONTROL_EVIDENCE_RESOURCE
                SET placeholder_ref = ?, label = ?, updated_at = ?
                WHERE resource_id = ?
                """,
                (placeholder, slot["label"], now, existing["resource_id"]),
            )
            continue
        next_id = conn.execute(
            "SELECT COALESCE(MAX(resource_id), 0) + 1 AS n FROM FCT_CONTROL_EVIDENCE_RESOURCE"
        ).fetchone()["n"]
        conn.execute(
            """
            INSERT INTO FCT_CONTROL_EVIDENCE_RESOURCE
              (resource_id, control_id, resource_key, label, placeholder_ref,
               document_url, document_title, workflow_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?)
            """,
            (
                next_id,
                control_id,
                slot["resource_key"],
                slot["label"],
                placeholder,
                now,
                now,
            ),
        )


def link_workflow_to_resource(
    conn: sqlite3.Connection,
    *,
    control_id: int,
    workflow_type: str,
    workflow_id: int,
    artifact_ref: str,
) -> None:
    key = workflow_type if workflow_type in {s["resource_key"] for s in RESOURCE_SLOT_DEFS} else workflow_type
    row = conn.execute(
        """
        SELECT resource_id FROM FCT_CONTROL_EVIDENCE_RESOURCE
        WHERE control_id = ? AND resource_key = ?
        """,
        (control_id, key),
    ).fetchone()
    if not row:
        return
    conn.execute(
        """
        UPDATE FCT_CONTROL_EVIDENCE_RESOURCE
        SET workflow_id = ?, placeholder_ref = ?, updated_at = ?
        WHERE resource_id = ?
        """,
        (workflow_id, artifact_ref, _utc_now_iso(), row["resource_id"]),
    )


def list_evidence_resources(conn: sqlite3.Connection, control_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT r.resource_id, r.control_id, r.resource_key, r.label, r.placeholder_ref,
               r.document_url, r.document_title, r.workflow_id, r.created_at, r.updated_at,
               w.status AS workflow_status, w.artifact_ref AS workflow_artifact_ref
        FROM FCT_CONTROL_EVIDENCE_RESOURCE r
        LEFT JOIN FCT_CONTROL_WORKFLOW w ON w.workflow_id = r.workflow_id
        WHERE r.control_id = ?
        ORDER BY r.resource_id
        """,
        (control_id,),
    ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["is_linked"] = bool(item.get("document_url") and str(item["document_url"]).strip())
        item["has_workflow"] = item.get("workflow_id") is not None
        item["link_state"] = (
            "document_linked"
            if item["is_linked"]
            else ("workflow_started" if item["has_workflow"] else "placeholder")
        )
        out.append(item)
    return out


def update_resource_document(
    conn: sqlite3.Connection,
    *,
    control_id: int,
    resource_id: int,
    document_url: str | None,
    document_title: str | None,
) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT resource_id FROM FCT_CONTROL_EVIDENCE_RESOURCE
        WHERE resource_id = ? AND control_id = ?
        """,
        (resource_id, control_id),
    ).fetchone()
    if row is None:
        return {"ok": False, "error": "not_found"}
    url = (document_url or "").strip() or None
    title = (document_title or "").strip() or None
    if url and not (url.startswith("http://") or url.startswith("https://")):
        return {"ok": False, "error": "invalid_url", "message": "Document URL must start with http:// or https://"}
    now = _utc_now_iso()
    conn.execute(
        """
        UPDATE FCT_CONTROL_EVIDENCE_RESOURCE
        SET document_url = ?, document_title = ?, updated_at = ?
        WHERE resource_id = ?
        """,
        (url, title, now, resource_id),
    )
    resources = list_evidence_resources(conn, control_id)
    updated = next((r for r in resources if r["resource_id"] == resource_id), None)
    return {"ok": True, "resource": updated}


def clear_resource_document(conn: sqlite3.Connection, *, control_id: int, resource_id: int) -> dict[str, Any]:
    return update_resource_document(
        conn, control_id=control_id, resource_id=resource_id, document_url=None, document_title=None
    )
