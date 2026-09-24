from __future__ import annotations

import json
import re
from datetime import date
from difflib import SequenceMatcher
from typing import Any

from banking_control.catalog import DOMAIN_OWNERS, ControlDefinition

RISK_TIERS: tuple[str, ...] = ("Critical", "High", "Medium", "Low")
FREQUENCIES: tuple[str, ...] = (
    "Event",
    "Daily",
    "Weekly",
    "Monthly",
    "Quarterly",
    "Annual",
)

REQUIRED_CREATE_FIELDS: tuple[str, ...] = (
    "control_name",
    "domain",
    "risk_tier",
    "owner",
    "frequency",
    "description",
)


def form_options() -> dict[str, Any]:
    return {
        "domains": [
            {"code": code, "default_owner": owner}
            for code, owner in sorted(DOMAIN_OWNERS.items())
        ],
        "risk_tiers": list(RISK_TIERS),
        "frequencies": list(FREQUENCIES),
    }


def validate_create_payload(body: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_CREATE_FIELDS:
        val = body.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(f"{field} is required")
    domain = str(body.get("domain") or "").strip().upper()
    if domain and domain not in DOMAIN_OWNERS:
        errors.append(f"domain must be one of: {', '.join(sorted(DOMAIN_OWNERS))}")
    risk = str(body.get("risk_tier") or "").strip()
    if risk and risk not in RISK_TIERS:
        errors.append(f"risk_tier must be one of: {', '.join(RISK_TIERS)}")
    freq = str(body.get("frequency") or "").strip()
    if freq and freq not in FREQUENCIES:
        errors.append(f"frequency must be one of: {', '.join(FREQUENCIES)}")
    name = str(body.get("control_name") or "").strip()
    if name and len(name) < 8:
        errors.append("control_name should be at least 8 characters")
    desc = str(body.get("description") or "").strip()
    if desc and len(desc) < 40:
        errors.append("description should be at least 40 characters")
    code = body.get("control_code")
    if code is not None and str(code).strip():
        if not re.match(r"^[A-Z]{2,8}-\d{3,4}$", str(code).strip().upper()):
            errors.append("control_code must match DOMAIN-NNN (e.g. AML-042)")
    return errors


def allocate_control_code(conn: Any, domain: str) -> str:
    dom = domain.strip().upper()
    row = conn.execute(
        """
        SELECT control_code FROM DIM_CONTROL
        WHERE domain = ? AND control_code GLOB ?
        ORDER BY control_code DESC LIMIT 1
        """,
        (dom, f"{dom}-*"),
    ).fetchone()
    next_num = 1
    if row:
        match = re.search(r"-(\d+)$", row["control_code"])
        if match:
            next_num = int(match.group(1)) + 1
    return f"{dom}-{next_num:03d}"


def _token_set(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-zA-Z]{3,}", text)}


def find_similar_controls(
    conn: Any,
    *,
    control_name: str,
    description: str,
    domain: str | None = None,
    limit: int = 8,
) -> list[dict[str, Any]]:
    name = control_name.strip()
    desc = description.strip()
    query_tokens = _token_set(f"{name} {desc}")
    clauses: list[str] = []
    params: list[Any] = []
    if domain:
        clauses.append("domain = ?")
        params.append(domain.strip().upper())
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"""
        SELECT control_id, control_code, control_name, domain, risk_tier,
               similarity_key, description, is_golden
        FROM DIM_CONTROL
        {where}
        ORDER BY is_golden DESC, control_code
        LIMIT 400
        """,
        params,
    ).fetchall()
    scored: list[tuple[float, dict[str, Any]]] = []
    for row in rows:
        r = dict(row)
        catalog_text = f"{r['control_name']} {r.get('description') or ''}"
        name_ratio = SequenceMatcher(None, name.lower(), r["control_name"].lower()).ratio()
        token_overlap = len(query_tokens & _token_set(catalog_text)) / max(1, len(query_tokens))
        domain_bonus = 0.12 if domain and r["domain"] == domain.strip().upper() else 0.0
        score = name_ratio * 0.55 + token_overlap * 0.35 + domain_bonus
        if score < 0.18 and not domain_bonus:
            continue
        relation = "similar_objective"
        relation_label = "Similar wording / objective"
        if name_ratio > 0.82:
            relation = "possible_duplicate"
            relation_label = "Possible duplicate name"
        elif r.get("similarity_key") and token_overlap > 0.25:
            relation = "same_theme"
            relation_label = "Same harmonization theme"
        scored.append(
            (
                score,
                {
                    **r,
                    "score": round(score, 3),
                    "relation": relation,
                    "relation_label": relation_label,
                },
            )
        )
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]


def compare_to_catalog(
    conn: Any,
    *,
    control_name: str,
    description: str,
    domain: str,
    control_code: str | None = None,
) -> dict[str, Any]:
    similar = find_similar_controls(
        conn,
        control_name=control_name,
        description=description,
        domain=domain,
        limit=12,
    )
    warnings: list[str] = []
    duplicates = [s for s in similar if s["relation"] == "possible_duplicate"]
    if duplicates:
        warnings.append(
            "Catalog already contains controls with very similar names; review before creating."
        )
    if control_code:
        exists = conn.execute(
            "SELECT 1 FROM DIM_CONTROL WHERE control_code = ?",
            (control_code.upper(),),
        ).fetchone()
        if exists:
            warnings.append(f"Control code {control_code.upper()} is already in use.")
    same_domain = conn.execute(
        "SELECT COUNT(*) AS n FROM DIM_CONTROL WHERE domain = ?",
        (domain.strip().upper(),),
    ).fetchone()["n"]
    return {
        "similar_controls": similar,
        "warnings": warnings,
        "catalog_stats": {"domain_control_count": int(same_domain)},
    }


def llm_control_recommendations(
    conn: Any,
    *,
    control_name: str,
    description: str,
    domain: str,
    similar_controls: list[dict[str, Any]],
) -> dict[str, Any]:
    from banking_control.llm.router import is_llm_configured, stream_text_chunks

    if not is_llm_configured(conn):
        return {
            "provider": None,
            "summary": (
                "LLM is offline — use the rule-based similar controls list below. "
                "Align similarity_key with peers when harmonizing testing."
            ),
            "suggested_similarity_key": _suggest_similarity_key(similar_controls),
        }

    peers = "\n".join(
        f"- {c['control_code']}: {c['control_name']} ({c['relation_label']})"
        for c in similar_controls[:6]
    )
    system = (
        "You advise banking control catalog designers. Be concise. "
        "Respond in plain markdown (2-4 short bullets). Mention overlap risk and "
        "whether to reuse a similarity group."
    )
    user = (
        f"Proposed control:\n"
        f"- Domain: {domain}\n"
        f"- Name: {control_name}\n"
        f"- Description: {description[:1200]}\n\n"
        f"Catalog peers:\n{peers or '(none)'}\n\n"
        "Comment on related controls and harmonization."
    )
    chunks = list(stream_text_chunks(conn, system_prompt=system, user_prompt=user))
    text = "".join(chunks).strip()
    return {
        "provider": "configured",
        "summary": text or "No additional LLM commentary.",
        "suggested_similarity_key": _suggest_similarity_key(similar_controls),
    }


def _suggest_similarity_key(similar: list[dict[str, Any]]) -> str | None:
    keys: dict[str, int] = {}
    for row in similar:
        key = row.get("similarity_key")
        if key:
            keys[key] = keys.get(key, 0) + 1
    if not keys:
        return None
    return max(keys.items(), key=lambda kv: kv[1])[0]


def insert_control(
    conn: Any,
    *,
    control_code: str,
    control_name: str,
    domain: str,
    risk_tier: str,
    owner: str,
    frequency: str,
    description: str,
    similarity_key: str | None = None,
) -> int:
    next_id = conn.execute("SELECT COALESCE(MAX(control_id), 0) + 1 FROM DIM_CONTROL").fetchone()[0]
    conn.execute(
        """
        INSERT INTO DIM_CONTROL
          (control_id, control_code, control_name, domain, risk_tier, owner,
           frequency, description, is_golden, similarity_key, standards_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, NULL)
        """,
        (
            next_id,
            control_code.upper(),
            control_name.strip(),
            domain.strip().upper(),
            risk_tier,
            owner.strip(),
            frequency,
            description.strip(),
            similarity_key,
        ),
    )
    return int(next_id)


def record_initial_assessment(
    conn: Any,
    *,
    control_id: int,
    status: str,
    tester: str,
    notes: str,
) -> None:
    unit = conn.execute(
        "SELECT unit_id FROM DIM_BUSINESS_UNIT ORDER BY unit_id LIMIT 1"
    ).fetchone()
    if unit is None:
        return
    next_assessment = conn.execute(
        "SELECT COALESCE(MAX(assessment_id), 0) + 1 FROM FCT_CONTROL_ASSESSMENT"
    ).fetchone()[0]
    conn.execute(
        """
        INSERT INTO FCT_CONTROL_ASSESSMENT
          (assessment_id, control_id, unit_id, assessment_date, status, tester, evidence_ref, notes)
        VALUES (?, ?, ?, date('now'), ?, ?, ?, ?)
        """,
        (
            next_assessment,
            control_id,
            unit["unit_id"],
            status,
            tester,
            "CREATE-SIM",
            notes[:2000],
        ),
    )


def definition_from_row(row: dict[str, Any]) -> ControlDefinition:
    return ControlDefinition(
        control_code=row["control_code"],
        control_name=row["control_name"],
        domain=row["domain"],
        risk_tier=row["risk_tier"],
        owner=row["owner"],
        frequency=row["frequency"],
        description=row["description"],
        is_golden=False,
        similarity_key=row.get("similarity_key"),
    )


def default_simulation_inputs() -> dict[str, Any]:
    return {
        "business_unit_code": "RB-EU",
        "period_end": date.today().isoformat(),
        "sample_size": 50,
        "evidence_refs": ["create-control-workpaper"],
        "context": {"source": "control_create_flow"},
    }
