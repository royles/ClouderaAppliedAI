from __future__ import annotations

import hashlib
import json
from typing import Any

from banking_control.tools.models import ControlTool


def stable_roll(seed: str, low: float = 0.0, high: float = 1.0) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    unit = int(digest[:8], 16) / 0xFFFFFFFF
    return low + (high - low) * unit


def status_from_roll(roll: float) -> str:
    if roll < 0.72:
        return "Effective"
    if roll < 0.87:
        return "Partially Effective"
    if roll < 0.95:
        return "Ineffective"
    return "Not Tested"


class GenericSimulator:
    priority = 0

    def matches(self, tool: ControlTool) -> bool:
        return True

    def simulate(self, tool: ControlTool, inputs: dict[str, Any]) -> dict[str, Any]:
        bu = str(inputs.get("business_unit_code", "GRP-EU"))
        sample = int(inputs.get("sample_size", 30))
        seed = (
            f"{tool.control_code}:{bu}:{sample}:"
            f"{json.dumps(inputs.get('context') or {}, sort_keys=True)}"
        )
        roll = stable_roll(seed)
        status = status_from_roll(roll)
        findings: list[dict[str, str]] = []
        if status != "Effective":
            findings.append(
                {
                    "severity": "Medium" if status == "Partially Effective" else "High",
                    "detail": f"Sample of {sample} items in {bu} produced exceptions in simulation.",
                }
            )
        return {
            "control_code": tool.control_code,
            "status": status,
            "summary": f"{tool.control_name} — simulated test outcome.",
            "findings": findings,
            "metrics": {"exception_rate_pct": round(roll * 15, 2), "sample_size": float(sample)},
            "simulated": True,
        }
