"""Format admin KPI benchmarks vs live portfolio KPIs for the copilot."""

from __future__ import annotations

from typing import Any

import sqlite3

from customer360.kpi_benchmarks import benchmarks_by_key


def _format_value(value: float, unit_kind: str) -> str:
    if unit_kind == "money":
        return f"₪{value:,.0f}"
    if unit_kind == "ratio":
        return f"{value * 100:.2f}%"
    if unit_kind == "percent":
        return f"{value:.1f}%"
    if unit_kind == "integer":
        return f"{int(round(value)):,}"
    return f"{value:,.2f}"


def benchmark_assessments_for_targets(
    conn: sqlite3.Connection,
    kpi_targets: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    lookup = benchmarks_by_key(conn, ensure_catalog=True)
    assessments: list[dict[str, Any]] = []
    for key, prog in kpi_targets.items():
        bench = lookup.get(key)
        if bench is None or not bench.enabled:
            continue
        status = str(prog.get("status") or "")
        direction = bench.direction
        actual = float(prog.get("actual") or 0)
        target = float(prog.get("target") or 0)
        amber = float(prog.get("amber_threshold") or bench.amber_threshold)
        unit = bench.unit_kind

        if status == "amber":
            if direction == "higher":
                vs = "below target but at/above amber floor (amber band)"
            else:
                vs = "above target but within amber band (worse than green, not yet red)"
        elif status == "red":
            vs = "below amber floor" if direction == "higher" else "above amber ceiling (red)"
        else:
            vs = "meets target (green)"

        assessments.append(
            {
                "kpi_key": key,
                "label": bench.display_label,
                "unit_kind": unit,
                "direction": direction,
                "actual": actual,
                "target": target,
                "status": status,
                "amber_threshold": amber,
                "progress_pct": prog.get("progress_pct"),
                "actual_display": _format_value(actual, unit),
                "target_display": _format_value(target, unit),
                "vs_target_summary": vs,
            }
        )
    return assessments


def format_benchmark_snippet(assessments: list[dict[str, Any]]) -> str | None:
    if not assessments:
        return None
    notable = [a for a in assessments if a.get("status") in ("amber", "red")]
    if not notable:
        return (
            "KPI vs admin benchmarks: "
            + ", ".join(
                f"{a['label']} {a['actual_display']} (target {a['target_display']}, green)"
                for a in assessments[:5]
            )
            + "."
        )
    parts = [
        f"{a['label']} {a['actual_display']} vs target {a['target_display']} "
        f"— {a['status'].upper()}: {a['vs_target_summary']}"
        for a in notable
    ]
    return "KPI benchmark context: " + "; ".join(parts) + "."
