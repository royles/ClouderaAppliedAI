from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from banking_control.control_workflows import (
    suggested_workflows_for_control,
    WORKFLOW_TYPES,
)

_EFFECTIVE_BASE = [
    "Control operation matches the catalog objective and documented frequency.",
    "Testing sample is defined and traceable (population, selection method, period).",
    "Exceptions are logged, root-caused, and tracked to remediation where applicable.",
]


def _parse_standards(raw: str | None) -> list[dict[str, str]]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONError:
        return []
    if not isinstance(data, list):
        return []
    out: list[dict[str, str]] = []
    for item in data:
        if isinstance(item, dict) and item.get("label") and item.get("url"):
            out.append({"label": str(item["label"]), "url": str(item["url"])})
    return out


def _requirements_from_description(description: str) -> list[str]:
    text = (description or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    reqs: list[str] = []
    for part in parts:
        p = part.strip()
        if not p:
            continue
        lower = p.lower()
        if any(
            k in lower
            for k in (
                "must",
                "shall",
                "requires",
                "evidence",
                "board",
                "annual",
                "document",
                "track",
                "monitor",
                "approve",
            )
        ):
            reqs.append(p)
    return reqs[:8]


def build_effective_checklist(
    *,
    control_name: str,
    description: str,
    standards_refs: list[dict[str, str]],
) -> list[dict[str, Any]]:
    checklist: list[dict[str, Any]] = []
    for base in _EFFECTIVE_BASE:
        checklist.append(
            {
                "requirement": base,
                "regulatory_references": standards_refs[:3],
            }
        )
    for req in _requirements_from_description(description):
        checklist.append(
            {
                "requirement": req,
                "regulatory_references": standards_refs,
            }
        )
    for ref in standards_refs:
        checklist.append(
            {
                "requirement": f"Map control design and testing to: {ref['label']}",
                "regulatory_references": [ref],
            }
        )
    if not checklist:
        checklist.append(
            {
                "requirement": f"Demonstrate {control_name} operates as described in the control catalog.",
                "regulatory_references": [],
            }
        )
    return checklist


def fetch_control_grounding(conn: sqlite3.Connection, control_code: str) -> dict[str, Any]:
    code = control_code.strip().upper()
    row = conn.execute(
        """
        SELECT control_id, control_code, control_name, domain, risk_tier, owner,
               frequency, description, standards_json
        FROM DIM_CONTROL
        WHERE control_code = ? COLLATE NOCASE
        """,
        (code,),
    ).fetchone()
    if row is None:
        return {"found": False, "control_code": code}

    standards_refs = _parse_standards(row["standards_json"])
    latest = conn.execute(
        """
        SELECT status, assessment_date, tester, evidence_ref, notes
        FROM FCT_CONTROL_ASSESSMENT
        WHERE control_id = ?
        ORDER BY assessment_date DESC LIMIT 1
        """,
        (row["control_id"],),
    ).fetchone()

    assessments = []
    if latest:
        assessments.append(
            {
                "status": latest["status"],
                "assessment_date": latest["assessment_date"],
                "tester": latest["tester"],
                "evidence_ref": latest["evidence_ref"],
                "notes": latest["notes"],
            }
        )

    description = row["description"] or ""
    workflow_suggestions = suggested_workflows_for_control(
        conn, control_code=row["control_code"], description=description
    )
    return {
        "found": True,
        "control": {
            "control_id": row["control_id"],
            "control_code": row["control_code"],
            "control_name": row["control_name"],
            "domain": row["domain"],
            "risk_tier": row["risk_tier"],
            "owner": row["owner"],
            "frequency": row["frequency"],
            "description": description,
        },
        "standards_refs": standards_refs,
        "latest_assessment": assessments[0] if assessments else None,
        "effective_status_checklist": build_effective_checklist(
            control_name=row["control_name"],
            description=description,
            standards_refs=standards_refs,
        ),
        "workflow_suggestions": workflow_suggestions,
        "workflow_policy": (
            "Evidence IDs such as workpapers exist only after a workflow is started via "
            "start_control_workflow or the dashboard. Do not claim artifacts already exist unless "
            "artifact_ref is present in tool JSON."
        ),
        "workflow_types": WORKFLOW_TYPES,
    }


def wrap_simulation_response(
    conn: sqlite3.Connection,
    *,
    control_code: str,
    inputs: dict[str, Any],
    simulation_payload: dict[str, Any],
) -> dict[str, Any]:
    grounding = fetch_control_grounding(conn, control_code)
    outputs = simulation_payload.get("outputs") or {}
    evidence_from_inputs = list(inputs.get("evidence_refs") or [])
    return {
        "simulation": simulation_payload,
        "grounding": grounding,
        "simulation_disclaimer": (
            "Simulation metrics (status, exception_rate_pct, findings) are deterministic demo "
            "outputs only — not results from your production systems."
        ),
        "evidence_policy": {
            "do_not_invent_workpapers": True,
            "allowed_evidence_refs": evidence_from_inputs,
            "warehouse_evidence_ref": (
                grounding.get("latest_assessment", {}) or {}
            ).get("evidence_ref"),
            "instruction": (
                "Do not invent workpaper IDs, board packs, or customer data. "
                "Only cite evidence_refs listed in allowed_evidence_refs or warehouse_evidence_ref."
            ),
        },
        "simulated_status": outputs.get("status"),
        "simulated_metrics": outputs.get("metrics"),
        "simulated_findings": outputs.get("findings"),
    }
