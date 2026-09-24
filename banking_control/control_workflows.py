"""Control testing workflows — create evidence artifacts instead of inventing IDs."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from typing import Any

WORKFLOW_STATUSES = ("Draft", "In Progress", "Complete", "Cancelled")

WORKFLOW_TYPES: dict[str, dict[str, str]] = {
    "testing_workpaper": {
        "label": "Control testing workpaper",
        "description": "Open a draft workpaper to document sample selection, procedures, and findings.",
    },
    "board_approval": {
        "label": "Board / committee approval pack",
        "description": "Track board or committee sign-off required by the control narrative.",
    },
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def proposed_artifact_ref(control_code: str, workflow_type: str, *, year: int | None = None) -> str:
    code = control_code.strip().upper()
    y = year or date.today().year
    if workflow_type == "testing_workpaper":
        return f"WP-{y}-{code}-RB"
    if workflow_type == "board_approval":
        return f"BOARD-APPROVAL-{y}-Q4"
    return f"WF-{y}-{code}-{workflow_type.upper()}"


def _control_row(conn: sqlite3.Connection, control_code: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT control_id, control_code, control_name FROM DIM_CONTROL WHERE control_code = ? COLLATE NOCASE",
        (control_code.strip().upper(),),
    ).fetchone()


def find_workflow_by_artifact(conn: sqlite3.Connection, artifact_ref: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT workflow_id, control_id, workflow_type, status, artifact_ref, created_at, updated_at
        FROM FCT_CONTROL_WORKFLOW
        WHERE artifact_ref = ?
        """,
        (artifact_ref,),
    ).fetchone()


def list_workflows_for_control(conn: sqlite3.Connection, control_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT workflow_id, workflow_type, status, artifact_ref, created_at, updated_at, metadata_json
        FROM FCT_CONTROL_WORKFLOW
        WHERE control_id = ?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (control_id,),
    ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        meta = item.pop("metadata_json", None)
        if meta:
            try:
                item["metadata"] = json.loads(meta)
            except json.JSONDecodeError:
                item["metadata"] = {}
        else:
            item["metadata"] = {}
        item["label"] = WORKFLOW_TYPES.get(item["workflow_type"], {}).get("label", item["workflow_type"])
        out.append(item)
    return out


def suggested_workflows_for_control(
    conn: sqlite3.Connection,
    *,
    control_code: str,
    description: str,
) -> list[dict[str, Any]]:
    """Grounded workflow triggers derived from catalog text — refs exist only after create."""
    code = control_code.strip().upper()
    desc_lower = (description or "").lower()
    suggestions: list[dict[str, Any]] = []

    wp_ref = proposed_artifact_ref(code, "testing_workpaper")
    existing_wp = find_workflow_by_artifact(conn, wp_ref)
    suggestions.append(
        {
            "workflow_type": "testing_workpaper",
            "label": WORKFLOW_TYPES["testing_workpaper"]["label"],
            "action": "open" if existing_wp else "create",
            "artifact_ref": existing_wp["artifact_ref"] if existing_wp else None,
            "proposed_artifact_ref": wp_ref if not existing_wp else None,
            "status": existing_wp["status"] if existing_wp else None,
        }
    )

    if "board" in desc_lower or "committee" in desc_lower:
        board_ref = proposed_artifact_ref(code, "board_approval")
        existing_board = find_workflow_by_artifact(conn, board_ref)
        suggestions.append(
            {
                "workflow_type": "board_approval",
                "label": WORKFLOW_TYPES["board_approval"]["label"],
                "action": "open" if existing_board else "create",
                "artifact_ref": existing_board["artifact_ref"] if existing_board else None,
                "proposed_artifact_ref": board_ref if not existing_board else None,
                "status": existing_board["status"] if existing_board else None,
            }
        )
    return suggestions


def start_workflow(
    conn: sqlite3.Connection,
    *,
    control_code: str,
    workflow_type: str,
    actor: str = "assistant",
) -> dict[str, Any]:
    if workflow_type not in WORKFLOW_TYPES:
        return {
            "ok": False,
            "error": "unknown_workflow_type",
            "workflow_type": workflow_type,
            "allowed": list(WORKFLOW_TYPES.keys()),
        }
    row = _control_row(conn, control_code)
    if row is None:
        return {"ok": False, "error": "unknown_control_code", "control_code": control_code}

    artifact_ref = proposed_artifact_ref(row["control_code"], workflow_type)
    existing = find_workflow_by_artifact(conn, artifact_ref)
    if existing:
        return {
            "ok": True,
            "created": False,
            "workflow": dict(existing),
            "control_code": row["control_code"],
            "control_id": int(row["control_id"]),
            "message": f"Workflow already exists for {artifact_ref}.",
        }

    now = _utc_now_iso()
    next_id = conn.execute(
        "SELECT COALESCE(MAX(workflow_id), 0) + 1 AS n FROM FCT_CONTROL_WORKFLOW"
    ).fetchone()["n"]
    meta = {
        "control_name": row["control_name"],
        "workflow_label": WORKFLOW_TYPES[workflow_type]["label"],
    }
    conn.execute(
        """
        INSERT INTO FCT_CONTROL_WORKFLOW
          (workflow_id, control_id, workflow_type, status, artifact_ref, created_at, updated_at, metadata_json)
        VALUES (?, ?, ?, 'Draft', ?, ?, ?, ?)
        """,
        (
            next_id,
            row["control_id"],
            workflow_type,
            artifact_ref,
            now,
            now,
            json.dumps(meta),
        ),
    )
    conn.execute(
        """
        INSERT INTO FCT_AUDIT_EVENT (event_id, event_at, actor, action, entity_type, entity_id, detail)
        VALUES (
          (SELECT COALESCE(MAX(event_id), 0) + 1 FROM FCT_AUDIT_EVENT),
          ?, ?, 'Workflow started', 'control_workflow', ?, ?
        )
        """,
        (
            now,
            actor,
            str(next_id),
            f"Started {workflow_type} for {row['control_code']} → {artifact_ref}",
        ),
    )
    workflow = {
        "workflow_id": int(next_id),
        "control_id": int(row["control_id"]),
        "workflow_type": workflow_type,
        "status": "Draft",
        "artifact_ref": artifact_ref,
        "created_at": now,
        "updated_at": now,
    }
    return {
        "ok": True,
        "created": True,
        "workflow": workflow,
        "control_code": row["control_code"],
        "control_id": int(row["control_id"]),
        "message": f"Created draft workflow artifact {artifact_ref}.",
    }
