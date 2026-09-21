"""Business KPI progress (thermometer) using APP_ADMIN_KPI_BENCHMARK lookup."""

from __future__ import annotations

import math
from typing import Any, Literal

from customer360.kpi_benchmarks import KpiBenchmarkRow, benchmarks_by_key, ensure_kpi_benchmark_catalog
from customer360.admin_store import admin_connect

Status = Literal["green", "amber", "red"]
Direction = Literal["higher", "lower"]


def _status_higher(actual: float, target: float, amber_ratio: float) -> Status:
    if target <= 0:
        return "amber"
    ratio = actual / target
    if ratio >= 1.0:
        return "green"
    if ratio >= amber_ratio:
        return "amber"
    return "red"


def _status_lower(actual: float, target: float, amber_multiplier: float) -> Status:
    if target <= 0:
        return "green" if actual <= 0 else "amber"
    if actual <= target:
        return "green"
    if actual <= target * amber_multiplier:
        return "amber"
    return "red"


def _progress_entry(
    *,
    target: float,
    actual: float,
    direction: Direction,
    amber_threshold: float,
) -> dict[str, Any]:
    if direction == "higher":
        progress_pct = round(min(100.0, 100.0 * actual / target), 1) if target > 0 else 0.0
        status = _status_higher(actual, target, amber_threshold)
    else:
        progress_pct = (
            round(min(100.0, 100.0 * target / actual), 1) if actual > 0 else 100.0
        )
        status = _status_lower(actual, target, amber_threshold)
    return {
        "target": round(float(target), 4),
        "actual": round(float(actual), 4),
        "progress_pct": progress_pct,
        "status": status,
        "direction": direction,
        "amber_threshold": amber_threshold,
    }


def _round_book_target(value: float) -> float:
    if value <= 0:
        return 0.0
    magnitude = 10 ** max(0, int(math.log10(value)) - 2)
    return round(math.ceil(value / magnitude) * magnitude, 2)


def _default_target_value(
    kpi_key: str,
    kpis: dict[str, Any],
    value_points: list[dict],
) -> float | None:
    total_book = float(kpis.get("total_book_value") or 0)
    active = int(kpis.get("active_customers") or 0)
    peak_book = total_book
    for pt in value_points:
        peak_book = max(peak_book, float(pt.get("total_value") or 0))

    if kpi_key == "total_book_value":
        return _round_book_target(max(peak_book * 1.12, total_book * 1.08, 1.0))
    if kpi_key == "active_customers":
        return float(max(int(math.ceil(active * 1.1 / 50) * 50), active + 1) if active else 100)
    if kpi_key == "annual_retention_rate_forecast":
        return 0.92
    if kpi_key == "value_at_risk_12m":
        return round(total_book * 0.08, 2) if total_book > 0 else 0.0
    if kpi_key == "avg_customer_value":
        avg_value = float(kpis.get("avg_customer_value") or 0)
        return round(max(avg_value * 1.1, avg_value + 1), 2) if avg_value > 0 else 0.0
    if kpi_key == "high_risk_book_pct":
        return 5.0
    if kpi_key == "book_growth_pct":
        return 8.0
    return None


def _resolve_target(
    bench: KpiBenchmarkRow,
    kpis: dict[str, Any],
    value_points: list[dict],
) -> float:
    if bench.target_value is not None and bench.target_value > 0:
        return float(bench.target_value)
    computed = _default_target_value(bench.kpi_key, kpis, value_points)
    return float(computed or 0)


def _kpi_actual(kpi_key: str, kpis: dict[str, Any]) -> float | None:
    if kpi_key == "annual_retention_rate_forecast":
        val = kpis.get("annual_retention_rate_forecast")
        return None if val is None else float(val)
    if kpi_key == "book_growth_pct":
        val = kpis.get("book_growth_pct")
        return None if val is None else float(val)
    if kpi_key not in kpis:
        return None
    return float(kpis.get(kpi_key) or 0)


def build_kpi_targets(
    kpis: dict[str, Any],
    value_points: list[dict] | None = None,
) -> dict[str, dict[str, Any]]:
    points = value_points or []
    conn = admin_connect()
    ensure_kpi_benchmark_catalog(conn)
    lookup = benchmarks_by_key(conn)
    conn.close()

    out: dict[str, dict[str, Any]] = {}
    for key, bench in lookup.items():
        if not bench.enabled:
            continue
        actual = _kpi_actual(key, kpis)
        if actual is None:
            continue
        target = _resolve_target(bench, kpis, points)
        if target <= 0:
            continue
        out[key] = _progress_entry(
            target=target,
            actual=actual,
            direction=bench.direction,
            amber_threshold=bench.amber_threshold,
        )
    return out
