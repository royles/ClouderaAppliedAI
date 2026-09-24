"""Structured workflow / artifact task cards for the assistant UI."""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from banking_control.control_workflows import WORKFLOW_TYPES, find_workflow_by_artifact

_ARTIFACT_REF = re.compile(
    r"\b(WP-\d{4}-[A-Z]{2,10}-\d{3}-RB|BOARD-APPROVAL-\d{4}-Q\d)\b",
    re.IGNORECASE,
)
_METADATA_LINE = re.compile(
    r"^(Artifact reference|Control:|Workflow type:|Status:|Created/Updated):.*$",
    re.MULTILINE | re.IGNORECASE,
)


def _document_link_for_placeholder(
    conn: sqlite3.Connection, control_id: int, placeholder_ref: str
) -> dict[str, Any] | None:
    doc = conn.execute(
        """
        SELECT document_url, document_title FROM FCT_CONTROL_EVIDENCE_RESOURCE
        WHERE control_id = ? AND placeholder_ref = ? COLLATE NOCASE
          AND document_url IS NOT NULL AND trim(document_url) != ''
        """,
        (control_id, placeholder_ref),
    ).fetchone()
    if not doc:
        return None
    title = doc["document_title"] or "Open linked document"
    return {
        "link_id": "document",
        "label": title,
        "kind": "document",
        "url": doc["document_url"],
    }


def _task_from_db_row(conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    wf_type = row["workflow_type"]
    label = WORKFLOW_TYPES.get(wf_type, {}).get("label", wf_type)
    control_id = int(row["control_id"])
    links: list[dict[str, Any]] = [
        {
            "link_id": "control_workflows",
            "label": f"Open {row['control_code']} · evidence",
            "kind": "control_detail",
            "control_id": control_id,
        },
    ]
    doc_link = _document_link_for_placeholder(conn, control_id, row["artifact_ref"])
    if doc_link:
        links.insert(0, doc_link)
    return {
        "task_id": f"workflow_{row['workflow_id']}",
        "exists": True,
        "artifact_ref": row["artifact_ref"],
        "workflow_id": int(row["workflow_id"]),
        "workflow_type": wf_type,
        "workflow_label": label,
        "status": row["status"],
        "control_code": row["control_code"],
        "control_id": control_id,
        "control_name": row["control_name"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "links": links,
    }


def lookup_workflow_task(conn: sqlite3.Connection, artifact_ref: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT w.workflow_id, w.control_id, w.workflow_type, w.status, w.artifact_ref,
               w.created_at, w.updated_at,
               c.control_code, c.control_name
        FROM FCT_CONTROL_WORKFLOW w
        JOIN DIM_CONTROL c ON c.control_id = w.control_id
        WHERE w.artifact_ref = ? COLLATE NOCASE
        """,
        (artifact_ref.strip(),),
    ).fetchone()
    if row is None:
        return None
    return _task_from_db_row(conn, row)


def _task_from_suggestion(
    conn: sqlite3.Connection,
    *,
    control_code: str,
    item: dict[str, Any],
) -> dict[str, Any] | None:
    ref = item.get("artifact_ref") or item.get("proposed_artifact_ref")
    if not ref:
        return None
    existing = lookup_workflow_task(conn, ref)
    if existing:
        return existing
    cid_row = conn.execute(
        "SELECT control_id, control_name FROM DIM_CONTROL WHERE control_code = ? COLLATE NOCASE",
        (control_code.strip().upper(),),
    ).fetchone()
    if cid_row is None:
        return None
    wf_type = item.get("workflow_type", "testing_workpaper")
    label = item.get("label") or WORKFLOW_TYPES.get(wf_type, {}).get("label", wf_type)
    return {
        "task_id": f"proposed_{wf_type}_{control_code}",
        "exists": False,
        "artifact_ref": ref,
        "proposed_artifact_ref": ref,
        "workflow_type": wf_type,
        "workflow_label": label,
        "status": None,
        "control_code": control_code,
        "control_id": int(cid_row["control_id"]),
        "control_name": cid_row["control_name"],
        "links": [
            {
                "link_id": "control_workflows",
                "label": f"Open {control_code} · workflows",
                "kind": "control_detail",
                "control_id": int(cid_row["control_id"]),
            },
        ],
    }


def _tasks_from_tool_messages(
    conn: sqlite3.Connection, messages: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for msg in messages:
        if msg.get("role") != "tool":
            continue
        try:
            data = json.loads(msg.get("content") or "")
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        if data.get("ok") and data.get("workflow"):
            wf = data["workflow"]
            ref = wf.get("artifact_ref")
            if ref:
                found = lookup_workflow_task(conn, ref)
                if found:
                    tasks.append(found)
                    continue
        if data.get("found") and data.get("workflow_suggestions"):
            ctrl = (data.get("control") or {}).get("control_code") or ""
            for item in data["workflow_suggestions"]:
                task = _task_from_suggestion(conn, control_code=ctrl, item=item)
                if task:
                    tasks.append(task)
    return tasks


def collect_workflow_tasks(
    conn: sqlite3.Connection,
    *,
    messages: list[dict[str, Any]] | None = None,
    answer_text: str = "",
    guide: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    by_ref: dict[str, dict[str, Any]] = {}
    for task in _tasks_from_tool_messages(conn, messages or []):
        by_ref[task["artifact_ref"].upper()] = task
    if guide and guide.get("found"):
        code = guide["control"]["control_code"]
        for item in guide.get("workflow_suggestions") or []:
            task = _task_from_suggestion(conn, control_code=code, item=item)
            if task:
                by_ref[task["artifact_ref"].upper()] = task
    for match in _ARTIFACT_REF.finditer(answer_text or ""):
        ref = match.group(1)
        found = lookup_workflow_task(conn, ref)
        if found:
            by_ref[ref.upper()] = found
        elif ref.upper() not in by_ref:
            # Mentioned in prose but not in DB — still show as pending if we can infer control
            code_m = re.search(r"WP-\d{4}-([A-Z]{2,10}-\d{3})-RB", ref, re.I)
            if code_m:
                task = _task_from_suggestion(
                    conn,
                    control_code=code_m.group(1),
                    item={
                        "workflow_type": "testing_workpaper",
                        "proposed_artifact_ref": ref,
                        "label": WORKFLOW_TYPES["testing_workpaper"]["label"],
                    },
                )
                if task:
                    by_ref[ref.upper()] = task
    return list(by_ref.values())


def dedupe_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for t in tasks:
        key = (t.get("artifact_ref") or "").upper()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


def strip_workflow_boilerplate_from_answer(text: str, tasks: list[dict[str, Any]]) -> str:
    """Remove duplicate metadata lines when task cards carry the same facts."""
    if not tasks or not text:
        return text
    out = _METADATA_LINE.sub("", text)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out
