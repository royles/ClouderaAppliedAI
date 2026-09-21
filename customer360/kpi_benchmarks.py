"""Lookup table for business KPI objectives and thermometer thresholds."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from customer360.admin_store import admin_connect, ensure_admin_schema

Direction = Literal["higher", "lower"]
UnitKind = Literal["money", "integer", "ratio", "percent"]

KPI_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "kpi_key": "total_book_value",
        "display_label": "Total book value",
        "direction": "higher",
        "unit_kind": "money",
        "amber_threshold": 0.85,
        "description": "Portfolio objective for total customer value (ILS).",
        "sort_order": 10,
    },
    {
        "kpi_key": "active_customers",
        "display_label": "Active customers",
        "direction": "higher",
        "unit_kind": "integer",
        "amber_threshold": 0.85,
        "description": "Book size objective for current customers in scope.",
        "sort_order": 20,
    },
    {
        "kpi_key": "annual_retention_rate_forecast",
        "display_label": "12m retention (forecast)",
        "direction": "higher",
        "unit_kind": "ratio",
        "amber_threshold": 0.98,
        "description": "Target annual retention rate (0–1, e.g. 0.92 = 92%).",
        "sort_order": 30,
    },
    {
        "kpi_key": "value_at_risk_12m",
        "display_label": "Value at churn risk",
        "direction": "lower",
        "unit_kind": "money",
        "amber_threshold": 1.2,
        "description": "Maximum acceptable 12-month value at risk (ILS).",
        "sort_order": 40,
    },
    {
        "kpi_key": "avg_customer_value",
        "display_label": "Avg customer value",
        "direction": "higher",
        "unit_kind": "money",
        "amber_threshold": 0.85,
        "description": "Average customer value objective (ILS).",
        "sort_order": 50,
    },
    {
        "kpi_key": "high_risk_book_pct",
        "display_label": "High-risk book share",
        "direction": "lower",
        "unit_kind": "percent",
        "amber_threshold": 1.2,
        "description": "Maximum % of book in HIGH churn tier.",
        "sort_order": 60,
    },
    {
        "kpi_key": "book_growth_pct",
        "display_label": "Book growth (history)",
        "direction": "higher",
        "unit_kind": "percent",
        "amber_threshold": 0.85,
        "description": "Historical book growth objective (%).",
        "sort_order": 70,
    },
)


@dataclass
class KpiBenchmarkRow:
    kpi_key: str
    display_label: str
    direction: Direction
    target_value: float | None
    amber_threshold: float
    unit_kind: UnitKind
    description: str | None
    sort_order: int
    enabled: bool
    updated_at: str | None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_benchmark(row: sqlite3.Row) -> KpiBenchmarkRow:
    return KpiBenchmarkRow(
        kpi_key=row["KPI_KEY"],
        display_label=row["DISPLAY_LABEL"],
        direction=row["DIRECTION"],
        target_value=row["TARGET_VALUE"],
        amber_threshold=float(row["AMBER_THRESHOLD"]),
        unit_kind=row["UNIT_KIND"],
        description=row["DESCRIPTION"],
        sort_order=int(row["SORT_ORDER"]),
        enabled=bool(row["ENABLED"]),
        updated_at=row["UPDATED_AT"],
    )


def ensure_kpi_benchmark_catalog(conn: sqlite3.Connection | None = None) -> None:
    own = conn is None
    if own:
        conn = admin_connect()
    else:
        ensure_admin_schema(conn)

    updated_at = _now_iso()
    for entry in KPI_CATALOG:
        conn.execute(
            """
            INSERT INTO APP_ADMIN_KPI_BENCHMARK (
                KPI_KEY, DISPLAY_LABEL, DIRECTION, TARGET_VALUE, AMBER_THRESHOLD,
                UNIT_KIND, DESCRIPTION, SORT_ORDER, ENABLED, UPDATED_AT
            ) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(KPI_KEY) DO NOTHING
            """,
            (
                entry["kpi_key"],
                entry["display_label"],
                entry["direction"],
                entry["amber_threshold"],
                entry["unit_kind"],
                entry.get("description"),
                entry["sort_order"],
                updated_at,
            ),
        )
    conn.commit()
    if own:
        conn.close()


def list_kpi_benchmarks(
    conn: sqlite3.Connection | None = None,
    *,
    ensure_catalog: bool = True,
) -> list[KpiBenchmarkRow]:
    own = conn is None
    if own:
        conn = admin_connect()
    else:
        ensure_admin_schema(conn)
    if ensure_catalog:
        ensure_kpi_benchmark_catalog(conn)
    rows = conn.execute(
        """
        SELECT * FROM APP_ADMIN_KPI_BENCHMARK
        ORDER BY SORT_ORDER, KPI_KEY
        """
    ).fetchall()
    if own:
        conn.close()
    return [_row_to_benchmark(r) for r in rows]


def benchmarks_by_key(
    conn: sqlite3.Connection | None = None,
    *,
    ensure_catalog: bool = False,
) -> dict[str, KpiBenchmarkRow]:
    return {
        row.kpi_key: row
        for row in list_kpi_benchmarks(conn, ensure_catalog=ensure_catalog)
    }


def save_kpi_benchmarks(
    updates: list[dict[str, Any]],
    *,
    conn: sqlite3.Connection | None = None,
) -> list[KpiBenchmarkRow]:
    own = conn is None
    if own:
        conn = admin_connect()
    else:
        ensure_admin_schema(conn)
    ensure_kpi_benchmark_catalog(conn)

    catalog_keys = {e["kpi_key"] for e in KPI_CATALOG}
    updated_at = _now_iso()

    for item in updates:
        key = str(item.get("kpi_key", "")).strip()
        if key not in catalog_keys:
            continue
        target = item.get("target_value")
        if target is not None and target != "":
            target_val = float(target)
            if target_val <= 0:
                target_val = None
        else:
            target_val = None

        amber = item.get("amber_threshold")
        amber_val = float(amber) if amber is not None else None
        enabled = item.get("enabled")

        label = item.get("display_label")
        description = item.get("description")

        sets = ["UPDATED_AT = ?"]
        params: list[Any] = [updated_at]

        if target_val is not None or "target_value" in item:
            sets.append("TARGET_VALUE = ?")
            params.append(target_val)

        if amber_val is not None:
            sets.append("AMBER_THRESHOLD = ?")
            params.append(amber_val)

        if enabled is not None:
            sets.append("ENABLED = ?")
            params.append(1 if enabled else 0)

        if label is not None and str(label).strip():
            sets.append("DISPLAY_LABEL = ?")
            params.append(str(label).strip())

        if description is not None:
            sets.append("DESCRIPTION = ?")
            params.append(str(description).strip() or None)

        params.append(key)
        conn.execute(
            f"UPDATE APP_ADMIN_KPI_BENCHMARK SET {', '.join(sets)} WHERE KPI_KEY = ?",
            params,
        )

    conn.commit()
    result = list_kpi_benchmarks(conn)
    if own:
        conn.close()
    return result


def benchmark_for_api(row: KpiBenchmarkRow) -> dict[str, Any]:
    return {
        "kpi_key": row.kpi_key,
        "display_label": row.display_label,
        "direction": row.direction,
        "target_value": row.target_value,
        "amber_threshold": row.amber_threshold,
        "unit_kind": row.unit_kind,
        "description": row.description,
        "sort_order": row.sort_order,
        "enabled": row.enabled,
        "updated_at": row.updated_at,
    }
