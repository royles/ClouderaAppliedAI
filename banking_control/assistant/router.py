"""Rule-based assistant answers and grounded dashboard action chips."""

from __future__ import annotations

import re
import sqlite3
from typing import Any

from banking_control.assistant.actions import (
    action_filter_alerts,
    action_filter_controls,
    action_focus_panel,
    action_metric_filter,
    action_open_control_code,
    action_open_detail,
)
from banking_control.db import get_overview
from banking_control.tools.engine import ControlToolEngine

_WORD = re.compile(r"[a-z0-9\-]+")


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def _control_id_by_code(conn: sqlite3.Connection, code: str) -> int | None:
    row = conn.execute(
        "SELECT control_id FROM DIM_CONTROL WHERE control_code = ? COLLATE NOCASE",
        (code.upper().replace("_", "-"),),
    ).fetchone()
    return int(row["control_id"]) if row else None


def _latest_alert_id(conn: sqlite3.Connection, *, status: str | None = None) -> int | None:
    if status:
        row = conn.execute(
            """
            SELECT alert_id FROM FCT_TRANSACTION_ALERT
            WHERE status = ? ORDER BY risk_score DESC, alert_at DESC LIMIT 1
            """,
            (status,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT alert_id FROM FCT_TRANSACTION_ALERT ORDER BY alert_at DESC LIMIT 1"
        ).fetchone()
    return int(row["alert_id"]) if row else None


def _latest_open_exception_id(conn: sqlite3.Connection) -> int | None:
    row = conn.execute(
        """
        SELECT exception_id FROM FCT_EXCEPTION
        WHERE status != 'Closed'
        ORDER BY
          CASE severity WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
          due_date
        LIMIT 1
        """
    ).fetchone()
    return int(row["exception_id"]) if row else None


def starter_actions(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    ov = get_overview(conn)
    new_alerts = (ov.get("alert_status") or {}).get("New", 0)
    return [
        action_metric_filter(
            "critical",
            label=f"Critical controls ({ov.get('critical_controls', 0)})",
        ),
        action_metric_filter(
            "alerts-new",
            label=f"New AML alerts ({new_alerts})",
        ),
        action_metric_filter(
            "exceptions",
            label=f"Open exceptions ({ov.get('open_exceptions', 0)})",
        ),
        action_filter_controls(
            label="Golden MVP catalog",
            golden_only=True,
        ),
    ]


def suggest_actions(
    conn: sqlite3.Connection,
    message: str,
    *,
    tools_called: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Grounded chips from user message (and optional tool names). Does not invent IDs."""
    text = (message or "").strip().lower()
    tokens = _tokens(text)
    actions: list[dict[str, Any]] = []
    tools_called = tools_called or []

    if "list_controls" in tools_called:
        if "aml" in tokens:
            actions.append(action_filter_controls(label="Filter catalog · AML domain", domain="AML"))
        if "kyc" in tokens:
            actions.append(action_filter_controls(label="Filter catalog · KYC domain", domain="KYC"))
        if "golden" in tokens:
            actions.append(action_filter_controls(label="Golden MVP controls only", golden_only=True))
        if "sanction" in text:
            actions.append(
                action_filter_controls(
                    label="Sanctions screening peers",
                    similarity_key="sanctions-screening",
                )
            )

    code_match = re.search(r"\b([A-Z]{2,10}-\d{3})\b", message.upper())
    if code_match:
        cid = _control_id_by_code(conn, code_match.group(1))
        if cid:
            actions.append(
                action_open_control_code(code_match.group(1), cid, label=f"Open {code_match.group(1)} detail")
            )

    if any(w in tokens for w in ("critical", "highest", "tier")):
        actions.append(action_metric_filter("critical", label="Filter · Critical controls"))
    if "exception" in text or "remediation" in text:
        actions.append(action_metric_filter("exceptions", label="Jump to open exceptions"))
        eid = _latest_open_exception_id(conn)
        if eid and ("detail" in text or "open" in text or "drill" in text):
            actions.append(
                action_open_detail("exceptions", eid, label="Open top open exception")
            )
    if "alert" in text or "aml" in text and "monitor" in text:
        actions.append(action_metric_filter("alerts-new", label="Filter · New AML alerts"))
        actions.append(action_focus_panel("panel-alerts", label="Focus transaction alerts panel"))
        if "detail" in text or "open" in text:
            aid = _latest_alert_id(conn, status="New" if "new" in text else None)
            if aid:
                actions.append(action_open_detail("alerts", aid, label="Open latest alert detail"))
    if "audit" in text or "trail" in text:
        actions.append(action_focus_panel("panel-audit", label="Focus audit trail"))
    if "health" in text or "effective" in text:
        actions.append(action_metric_filter("health", label="Controls needing attention"))
    if "golden" in text:
        actions.append(action_filter_controls(label="Golden MVP catalog", golden_only=True))
    if "simulate" in text or "test control" in text:
        actions.append(action_focus_panel("panel-controls", label="Open control catalog"))

    # Deduplicate by action_id
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for a in actions:
        aid = a.get("action_id", "")
        if aid in seen:
            continue
        seen.add(aid)
        unique.append(a)
    if unique:
        return unique[:4]
    return starter_actions(conn)[:4]


def answer_question_rules(
    conn: sqlite3.Connection,
    engine: ControlToolEngine,
    message: str,
) -> dict[str, Any]:
    del engine  # reserved for future tool-aware rules
    text = (message or "").strip()
    ov = get_overview(conn)

    if not text:
        return {
            "answer": (
                "I can help you explore live control tower data — KPIs, the control catalog, "
                "transaction alerts, exceptions, and audit events. "
                "Pick a shortcut below or ask in plain language (for example: “Show critical AML controls” "
                "or “Open AML-003”)."
            ),
            "actions": starter_actions(conn),
            "source": "rules",
        }

    lowered = text.lower()
    preamble_parts: list[str] = []

    if any(w in lowered for w in ("overview", "summary", "kpi", "health", "status")):
        preamble_parts.append(
            f"Control health is {ov.get('control_health_pct', 0)}% effective across tested controls, "
            f"with {ov.get('open_exceptions', 0)} open exceptions and "
            f"{(ov.get('alert_status') or {}).get('New', 0)} new AML alerts awaiting review."
        )

    actions = suggest_actions(conn, text)

    if code_match := re.search(r"\b([A-Z]{2,10}-\d{3})\b", text.upper()):
        cid = _control_id_by_code(conn, code_match.group(1))
        if cid:
            row = conn.execute(
                "SELECT control_name FROM DIM_CONTROL WHERE control_id = ?",
                (cid,),
            ).fetchone()
            name = row["control_name"] if row else code_match.group(1)
            answer = (
                " ".join(preamble_parts)
                + f" Opening control {code_match.group(1)} ({name}) in the detail view. "
                "The catalog and assessments are loaded from the warehouse API."
            ).strip()
            return {"answer": answer, "actions": actions[:4], "source": "rules"}

    if "critical" in lowered and ("control" in lowered or "catalog" in lowered):
        answer = (
            " ".join(preamble_parts)
            + f" There are {ov.get('critical_controls', 0)} critical-tier controls in the catalog. "
            "Use the link below to filter the control catalog and review test status."
        ).strip()
        return {"answer": answer, "actions": actions[:4], "source": "rules"}

    if "exception" in lowered:
        answer = (
            " ".join(preamble_parts)
            + f" {ov.get('open_exceptions', 0)} exceptions are open across remediation stages. "
            "You can jump to the exceptions panel or open a specific record."
        ).strip()
        return {"answer": answer, "actions": actions[:4], "source": "rules"}

    if "alert" in lowered or ("transaction" in lowered and "monitor" in lowered):
        new_n = (ov.get("alert_status") or {}).get("New", 0)
        answer = (
            " ".join(preamble_parts)
            + f" {new_n} transaction monitoring alerts are in New status. "
            "Filter the alerts panel or open a detail view for narrative and risk score."
        ).strip()
        return {"answer": answer, "actions": actions[:4], "source": "rules"}

    if "audit" in lowered:
        answer = (
            " ".join(preamble_parts)
            + " Recent audit trail events are listed on the dashboard. "
            "Focus the audit panel or ask about a specific control code to drill in."
        ).strip()
        return {"answer": answer, "actions": actions[:4], "source": "rules"}

    if "golden" in lowered:
        answer = (
            " ".join(preamble_parts)
            + f" The MVP golden set includes {ov.get('golden_controls', 80)} prioritized controls. "
            "Open the filtered catalog below."
        ).strip()
        return {"answer": answer, "actions": actions[:4], "source": "rules"}

    answer = (
        " ".join(preamble_parts)
        + " Here are grounded shortcuts based on your question and current warehouse data. "
        "Each link updates the main dashboard or opens an detail view — the assistant stays open."
    ).strip()
    if not preamble_parts:
        answer = (
            "I work from the live control tower APIs and tools (catalog, overview, audit, simulations). "
            + answer
        )

    return {"answer": answer, "actions": actions[:4], "source": "rules"}
