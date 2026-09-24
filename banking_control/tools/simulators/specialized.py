from __future__ import annotations

from typing import Any

from banking_control.tools.models import ControlTool
from banking_control.tools.simulators.base import stable_roll, status_from_roll


class SimilarityKeySimulator:
    """Routes simulation by ``similarity_key`` (pluggable special cases)."""

    priority = 30

    _KEYS = frozenset(
        {
            "sanctions-screening",
            "customer-due-diligence",
            "dual-control",
            "transaction-monitoring",
        }
    )

    def matches(self, tool: ControlTool) -> bool:
        return tool.similarity_key in self._KEYS

    def simulate(self, tool: ControlTool, inputs: dict[str, Any]) -> dict[str, Any]:
        key = tool.similarity_key
        if key == "sanctions-screening":
            return _sanctions(tool, inputs)
        if key == "customer-due-diligence":
            return _cdd(tool, inputs)
        if key == "dual-control":
            return _dual_control(tool, inputs)
        if key == "transaction-monitoring":
            return _transaction_monitoring(tool, inputs)
        raise RuntimeError(f"No handler for similarity key {key}")


def _sanctions(tool: ControlTool, inputs: dict[str, Any]) -> dict[str, Any]:
    ctx = inputs.get("context") or {}
    payment_id = str(ctx.get("payment_id", "UNKNOWN"))
    amount = float(ctx.get("amount_eur", 0))
    country = str(ctx.get("counterparty_country", "DE")).upper()
    seed = f"{tool.control_code}:{payment_id}:{amount}:{country}"
    roll = stable_roll(seed)
    hit = roll > 0.92 or country in {"KP", "IR", "SY"}
    status = "Effective" if not hit else ("Partially Effective" if roll < 0.97 else "Ineffective")
    findings: list[dict[str, str]] = []
    if hit:
        findings.append(
            {
                "severity": "High",
                "detail": f"Potential sanctions match on payment {payment_id}; analyst queue simulated.",
            }
        )
    return {
        "control_code": tool.control_code,
        "status": status,
        "summary": "Sanctions screening simulation completed.",
        "findings": findings,
        "metrics": {
            "screening_hit": 1.0 if hit else 0.0,
            "amount_eur": amount,
            "risk_score": round(roll, 4),
        },
        "simulated": True,
    }


def _cdd(tool: ControlTool, inputs: dict[str, Any]) -> dict[str, Any]:
    ctx = inputs.get("context") or {}
    customer_id = str(ctx.get("customer_id", "UNKNOWN"))
    ctype = str(ctx.get("customer_type", "retail"))
    risk = str(ctx.get("risk_rating", "medium"))
    seed = f"{tool.control_code}:{customer_id}:{ctype}:{risk}"
    roll = stable_roll(seed)
    status = status_from_roll(roll)
    if risk == "high" and roll > 0.6:
        status = "Partially Effective"
    findings = []
    if status != "Effective":
        findings.append(
            {
                "severity": "Medium",
                "detail": f"CDD file gap simulated for {customer_id} ({ctype}).",
            }
        )
    return {
        "control_code": tool.control_code,
        "status": status,
        "summary": "Customer due diligence simulation completed.",
        "findings": findings,
        "metrics": {"file_completeness_pct": round((1 - roll) * 100, 1)},
        "simulated": True,
    }


def _dual_control(tool: ControlTool, inputs: dict[str, Any]) -> dict[str, Any]:
    ctx = inputs.get("context") or {}
    maker = str(ctx.get("maker_user", ""))
    checker = str(ctx.get("checker_user", ""))
    amount = float(ctx.get("amount_eur", 0))
    txn = str(ctx.get("transaction_id", "TXN"))
    same_person = maker and checker and maker.lower() == checker.lower()
    over_limit = amount > 250_000
    status = "Effective"
    findings: list[dict[str, str]] = []
    if same_person:
        status = "Ineffective"
        findings.append({"severity": "Critical", "detail": "Maker and checker are the same user."})
    elif over_limit and not checker:
        status = "Ineffective"
        findings.append({"severity": "High", "detail": "High-value transaction missing checker."})
    return {
        "control_code": tool.control_code,
        "status": status,
        "summary": f"Dual-control check simulated for {txn}.",
        "findings": findings,
        "metrics": {"amount_eur": amount, "dual_control_breach": 1.0 if same_person else 0.0},
        "simulated": True,
    }


def _transaction_monitoring(tool: ControlTool, inputs: dict[str, Any]) -> dict[str, Any]:
    ctx = inputs.get("context") or {}
    alert_id = str(ctx.get("alert_id", "ALERT"))
    scenario = str(ctx.get("scenario_id", "GEN"))
    seed = f"{tool.control_code}:{alert_id}:{scenario}"
    roll = stable_roll(seed)
    escalated = roll > 0.75
    status = "Effective" if roll < 0.85 else "Partially Effective"
    return {
        "control_code": tool.control_code,
        "status": status,
        "summary": "Transaction monitoring scenario simulation completed.",
        "findings": (
            [{"severity": "High", "detail": f"Alert {alert_id} escalated in simulation."}]
            if escalated
            else []
        ),
        "metrics": {"alert_risk_score": round(roll, 4), "escalated": 1.0 if escalated else 0.0},
        "simulated": True,
    }
