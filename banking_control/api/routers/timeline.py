from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query

from banking_control.api.deps import get_db_connection

router = APIRouter(tags=["timeline"])

Granularity = Literal["day", "week", "month"]


def _parse_day(value: str) -> date:
    return date.fromisoformat(value[:10])


def _month_label(period_start: str) -> str:
    d = _parse_day(period_start)
    return d.strftime("%b %Y")


def _choose_granularity(min_d: date, max_d: date) -> Granularity:
    span = (max_d - min_d).days + 1
    if span > 1100:
        return "month"
    if span > 120:
        return "week"
    return "day"


def _bucket_expr(column: str, granularity: Granularity) -> str:
    if granularity == "month":
        return f"substr({column}, 1, 7)"
    if granularity == "day":
        return f"substr({column}, 1, 10)"
    # Week bucket keyed by Monday (ISO-style) for YYYY-MM-DD dates
    return f"date({column}, 'weekday 0', '-6 days')"


def _period_end(period_start: str, granularity: Granularity) -> str:
    start = _parse_day(period_start)
    if granularity == "month":
        if start.month == 12:
            end = date(start.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(start.year, start.month + 1, 1) - timedelta(days=1)
    elif granularity == "week":
        end = start + timedelta(days=6)
    else:
        end = start
    return end.isoformat()


def _aggregate_counts(
    conn: Any,
    *,
    table: str,
    time_column: str,
    granularity: Granularity,
    from_date: str | None,
    to_date: str | None,
) -> dict[str, int]:
    bucket = _bucket_expr(time_column, granularity)
    clauses: list[str] = []
    params: list[Any] = []
    if from_date:
        clauses.append(f"substr({time_column}, 1, 10) >= ?")
        params.append(from_date[:10])
    if to_date:
        clauses.append(f"substr({time_column}, 1, 10) <= ?")
        params.append(to_date[:10])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"""
        SELECT {bucket} AS bucket, COUNT(*) AS n
        FROM {table}
        {where}
        GROUP BY bucket
        ORDER BY bucket
        """,
        params,
    ).fetchall()
    out: dict[str, int] = {}
    for row in rows:
        key = str(row["bucket"])
        if granularity == "month" and len(key) == 7:
            key = f"{key}-01"
        out[key] = int(row["n"])
    return out


@router.get("/api/activity-timeline")
def activity_timeline(
    granularity: str = Query("auto", pattern="^(auto|day|week|month)$"),
    from_date: str | None = Query(None, description="Limit buckets to dates on/after (ISO)"),
    to_date: str | None = Query(None, description="Limit buckets to dates on/before (ISO)"),
    conn: Any = Depends(get_db_connection),
) -> dict[str, Any]:
    """
    Pre-aggregated activity buckets for the dashboard timeline.

    Returns counts only (scales to large warehouses); list endpoints apply the
    same date window when filtering tables.
    """
    bounds = conn.execute(
        """
        SELECT MIN(d) AS min_d, MAX(d) AS max_d FROM (
          SELECT substr(alert_at, 1, 10) AS d FROM FCT_TRANSACTION_ALERT
          UNION ALL
          SELECT substr(event_at, 1, 10) AS d FROM FCT_AUDIT_EVENT
        )
        """
    ).fetchone()
    min_raw, max_raw = bounds["min_d"], bounds["max_d"]
    if not min_raw or not max_raw:
        return {
            "granularity": "month",
            "range": {"min": None, "max": None},
            "buckets": [],
            "totals": {"alerts": 0, "audit_events": 0, "combined": 0},
        }

    min_d = _parse_day(min_raw)
    max_d = _parse_day(max_raw)
    g: Granularity
    if granularity == "auto":
        g = _choose_granularity(min_d, max_d)
    else:
        g = granularity  # type: ignore[assignment]

    alert_counts = _aggregate_counts(
        conn,
        table="FCT_TRANSACTION_ALERT",
        time_column="alert_at",
        granularity=g,
        from_date=from_date,
        to_date=to_date,
    )
    audit_counts = _aggregate_counts(
        conn,
        table="FCT_AUDIT_EVENT",
        time_column="event_at",
        granularity=g,
        from_date=from_date,
        to_date=to_date,
    )

    keys = sorted(set(alert_counts) | set(audit_counts))
    buckets: list[dict[str, Any]] = []
    total_alerts = 0
    total_audit = 0
    for key in keys:
        alerts = alert_counts.get(key, 0)
        audit = audit_counts.get(key, 0)
        total_alerts += alerts
        total_audit += audit
        period_start = key[:10]
        buckets.append(
            {
                "period_start": period_start,
                "period_end": _period_end(period_start, g),
                "label": _month_label(period_start) if g == "month" else period_start,
                "alerts": alerts,
                "audit_events": audit,
                "total": alerts + audit,
            }
        )

    return {
        "granularity": g,
        "range": {"min": min_d.isoformat(), "max": max_d.isoformat()},
        "bucket_count": len(buckets),
        "buckets": buckets,
        "totals": {
            "alerts": total_alerts,
            "audit_events": total_audit,
            "combined": total_alerts + total_audit,
        },
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    }
