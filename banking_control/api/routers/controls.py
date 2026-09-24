from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from banking_control.api.deps import get_db_connection, get_tool_engine, get_tool_registry
from banking_control.control_create import (
    FREQUENCIES,
    RISK_TIERS,
    allocate_control_code,
    compare_to_catalog,
    default_simulation_inputs,
    definition_from_row,
    find_similar_controls,
    form_options,
    insert_control,
    llm_control_recommendations,
    record_initial_assessment,
    validate_create_payload,
)
from banking_control.control_graph import build_process_graph, list_flows_for_control
from banking_control.db import refresh_overview_cache
from banking_control.tools.engine import ControlToolEngine, ToolValidationError
from banking_control.tools.registry import ToolRegistry

router = APIRouter(prefix="/api", tags=["controls"])


class ControlRecommendRequest(BaseModel):
    control_name: str = Field(..., min_length=3, max_length=200)
    description: str = Field("", max_length=8000)
    domain: str | None = Field(None, max_length=16)
    risk_tier: str | None = None


class ControlCreateRequest(BaseModel):
    control_name: str = Field(..., min_length=8, max_length=200)
    domain: str = Field(..., min_length=2, max_length=16)
    risk_tier: str
    owner: str = Field(..., min_length=2, max_length=120)
    frequency: str
    description: str = Field(..., min_length=40, max_length=8000)
    control_code: str | None = Field(None, max_length=16)
    similarity_key: str | None = Field(None, max_length=80)
    run_simulation: bool = True


@router.get("/controls/form-options")
def get_control_form_options() -> dict[str, Any]:
    return form_options()


@router.post("/controls/recommend")
def recommend_control(
    body: ControlRecommendRequest,
    conn: Any = Depends(get_db_connection),
) -> dict[str, Any]:
    domain = body.domain.strip().upper() if body.domain else None
    similar = find_similar_controls(
        conn,
        control_name=body.control_name,
        description=body.description,
        domain=domain,
    )
    llm = llm_control_recommendations(
        conn,
        control_name=body.control_name,
        description=body.description,
        domain=domain or (similar[0]["domain"] if similar else "AML"),
        similar_controls=similar,
    )
    return {
        "similar_controls": similar,
        "llm": llm,
        "suggested_similarity_key": llm.get("suggested_similarity_key"),
    }


@router.post("/controls")
def create_control(
    body: ControlCreateRequest,
    conn: Any = Depends(get_db_connection),
    engine: ControlToolEngine = Depends(get_tool_engine),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> dict[str, Any]:
    payload = body.model_dump()
    errors = validate_create_payload(payload)
    if body.risk_tier not in RISK_TIERS:
        errors.append(f"risk_tier must be one of: {', '.join(RISK_TIERS)}")
    if body.frequency not in FREQUENCIES:
        errors.append(f"frequency must be one of: {', '.join(FREQUENCIES)}")
    if errors:
        raise HTTPException(status_code=400, detail={"validation_errors": errors})

    domain = body.domain.strip().upper()
    control_code = (
        body.control_code.strip().upper()
        if body.control_code and body.control_code.strip()
        else allocate_control_code(conn, domain)
    )
    catalog_review = compare_to_catalog(
        conn,
        control_name=body.control_name,
        description=body.description,
        domain=domain,
        control_code=control_code,
    )
    if any("already in use" in w for w in catalog_review["warnings"]):
        raise HTTPException(status_code=409, detail=catalog_review)

    similarity_key = body.similarity_key
    if not similarity_key and catalog_review["similar_controls"]:
        similarity_key = catalog_review["similar_controls"][0].get("similarity_key")
    if isinstance(similarity_key, str):
        similarity_key = similarity_key.strip() or None

    control_id = insert_control(
        conn,
        control_code=control_code,
        control_name=body.control_name,
        domain=domain,
        risk_tier=body.risk_tier,
        owner=body.owner,
        frequency=body.frequency,
        description=body.description,
        similarity_key=similarity_key,
    )

    row = conn.execute(
        "SELECT * FROM DIM_CONTROL WHERE control_id = ?", (control_id,)
    ).fetchone()
    definition = definition_from_row(dict(row))
    registry.register_dynamic(definition)

    simulation: dict[str, Any] | None = None
    simulation_error: str | None = None
    if body.run_simulation:
        inputs = default_simulation_inputs()
        try:
            simulation = engine.invoke(control_code, inputs)
            outputs = simulation.get("outputs") or {}
            status = outputs.get("status") or "Not Tested"
            summary = outputs.get("summary") or "Initial create simulation"
            record_initial_assessment(
                conn,
                control_id=control_id,
                status=status,
                tester="Control create simulation",
                notes=summary,
            )
        except ToolValidationError as exc:
            simulation_error = str(exc)

    conn.execute(
        """
        INSERT INTO FCT_AUDIT_EVENT (event_at, actor, action, entity_type, entity_id, detail)
        VALUES (datetime('now'), 'dashboard_user', 'Control created', 'control', ?, ?)
        """,
        (
            str(control_id),
            f"{control_code} · {body.control_name[:80]}",
        ),
    )
    conn.commit()
    refresh_overview_cache(conn)

    return {
        "control_id": control_id,
        "control_code": control_code,
        "catalog_review": catalog_review,
        "simulation": simulation,
        "simulation_error": simulation_error,
        "validation": {"ok": True, "fields_checked": list(payload.keys())},
    }


@router.get("/controls")
def list_controls(
    domain: str | None = None,
    risk_tier: str | None = None,
    golden: bool | None = None,
    similarity_key: str | None = None,
    search: str | None = Query(None, max_length=120),
    latest_status: str | None = None,
    needs_attention: bool | None = None,
    limit: int = Query(100, le=500),
    conn: Any = Depends(get_db_connection),
) -> list[dict[str, Any]]:
    latest_status_sql = """
        (
          SELECT a.status FROM FCT_CONTROL_ASSESSMENT a
          WHERE a.control_id = c.control_id
          ORDER BY a.assessment_date DESC LIMIT 1
        )
    """
    clauses: list[str] = []
    params: list[Any] = []
    if search and search.strip():
        term = f"%{search.strip()}%"
        clauses.append(
            "(c.control_code LIKE ? OR c.control_name LIKE ? OR c.description LIKE ?)"
        )
        params.extend([term, term, term])
    if domain:
        clauses.append("c.domain = ?")
        params.append(domain)
    if risk_tier:
        clauses.append("c.risk_tier = ?")
        params.append(risk_tier)
    if golden is True:
        clauses.append("c.is_golden = 1")
    elif golden is False:
        clauses.append("c.is_golden = 0")
    if similarity_key:
        clauses.append("c.similarity_key = ?")
        params.append(similarity_key)
    if latest_status:
        clauses.append(f"COALESCE({latest_status_sql}, 'Not Tested') = ?")
        params.append(latest_status)
    if needs_attention is True:
        clauses.append(
            f"COALESCE({latest_status_sql}, 'Not Tested') != 'Effective'"
        )
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT c.control_id, c.control_code, c.control_name, c.domain, c.risk_tier,
               c.owner, c.frequency, c.is_golden, c.similarity_key,
               (
                 SELECT a.status FROM FCT_CONTROL_ASSESSMENT a
                 WHERE a.control_id = c.control_id
                 ORDER BY a.assessment_date DESC LIMIT 1
               ) AS latest_status
        FROM DIM_CONTROL c
        {where}
        ORDER BY c.is_golden DESC, c.risk_tier, c.control_code
        LIMIT ?
        """,
        params,
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/controls/{control_id}")
def get_control(
    control_id: int,
    conn: Any = Depends(get_db_connection),
) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM DIM_CONTROL WHERE control_id = ?",
        (control_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Control not found")

    latest = conn.execute(
        """
        SELECT status FROM FCT_CONTROL_ASSESSMENT
        WHERE control_id = ?
        ORDER BY assessment_date DESC LIMIT 1
        """,
        (control_id,),
    ).fetchone()
    assessments = conn.execute(
        """
        SELECT a.assessment_id, a.assessment_date, a.status, a.tester,
               a.evidence_ref, a.notes, u.unit_code, u.unit_name
        FROM FCT_CONTROL_ASSESSMENT a
        JOIN DIM_BUSINESS_UNIT u ON u.unit_id = a.unit_id
        WHERE a.control_id = ?
        ORDER BY a.assessment_date DESC
        LIMIT 20
        """,
        (control_id,),
    ).fetchall()
    exceptions = conn.execute(
        """
        SELECT e.exception_id, e.title, e.severity, e.status, e.opened_at,
               e.due_date, e.assignee, u.unit_code
        FROM FCT_EXCEPTION e
        JOIN DIM_BUSINESS_UNIT u ON u.unit_id = e.unit_id
        WHERE e.control_id = ?
        ORDER BY e.opened_at DESC
        LIMIT 25
        """,
        (control_id,),
    ).fetchall()
    control = dict(row)
    standards_refs: list[dict[str, str]] = []
    raw_standards = control.pop("standards_json", None)
    if raw_standards:
        try:
            standards_refs = json.loads(raw_standards)
        except json.JSONDecodeError:
            standards_refs = []
    control_code = control["control_code"]
    similarity_key = control.get("similarity_key")

    related: list[dict[str, Any]] = []
    if similarity_key:
        rel_rows = conn.execute(
            """
            SELECT control_id, control_code, control_name, domain, risk_tier, is_golden,
                   similarity_key
            FROM DIM_CONTROL
            WHERE similarity_key = ? AND control_code != ?
            ORDER BY is_golden DESC,
              CASE risk_tier
                WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4
              END,
              control_code
            LIMIT 16
            """,
            (similarity_key, control_code),
        ).fetchall()
        related = [
            {**dict(r), "relation": "same_objective", "relation_label": "Same control objective"}
            for r in rel_rows
        ]

    process_graph = build_process_graph(control_code)
    if process_graph:
        codes = {n["control_code"] for n in process_graph["nodes"]}
        placeholders = ",".join("?" for _ in codes)
        id_rows = conn.execute(
            f"""
            SELECT control_id, control_code, control_name, domain, risk_tier
            FROM DIM_CONTROL
            WHERE control_code IN ({placeholders})
            """,
            list(codes),
        ).fetchall()
        by_code = {r["control_code"]: dict(r) for r in id_rows}
        for node in process_graph["nodes"]:
            info = by_code.get(node["control_code"], {})
            node["control_id"] = info.get("control_id")
            node["control_name"] = info.get("control_name", node["control_code"])
            node["domain"] = info.get("domain")
            node["risk_tier"] = info.get("risk_tier")

    return {
        "control": control,
        "standards_refs": standards_refs,
        "latest_status": latest["status"] if latest else "Not Tested",
        "assessments": [dict(r) for r in assessments],
        "exceptions": [dict(r) for r in exceptions],
        "related_controls": related,
        "process_graph": process_graph,
        "process_flows": list_flows_for_control(control_code),
    }
