from __future__ import annotations

import os
import random
import sqlite3
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

ALERT_TYPES: tuple[str, ...] = (
    "Structuring pattern",
    "Velocity anomaly",
    "High-risk jurisdiction",
    "Dormant account reactivation",
    "Round-dollar wire cluster",
    "Unusual cash activity",
    "Peer-to-peer mule indicator",
    "Trade-based ML typology",
)

CHANNELS: tuple[str, ...] = (
    "Wire",
    "SEPA",
    "Branch Teller",
    "Mobile",
    "Instant Payment",
)

def alerts_per_day_mean() -> float:
    raw = os.environ.get("TM_ALERTS_PER_DAY", "120").strip()
    try:
        return max(20.0, float(raw))
    except ValueError:
        return 120.0


MIN_ALERT_POOL = 48

NARRATIVES: tuple[str, ...] = (
    "Monitoring rule fired on aggregated activity; analyst review required per policy.",
    "Scenario exceeded velocity threshold versus 30-day customer baseline.",
    "Counterparty jurisdiction flagged on internal high-risk corridor list.",
    "Multiple round-dollar credits followed by immediate outbound wires.",
    "Instant payment burst inconsistent with declared account purpose.",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_alert_at(value: str) -> datetime:
    s = str(value or "").strip()
    if "T" in s:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    day = date.fromisoformat(s[:10])
    return datetime.combine(day, time(23, 59, 59), tzinfo=timezone.utc)


# Retain TM alerts for demo/history (2-year rolling window).
ALERT_RETENTION_DAYS = 730.0


def expire_alerts_older_than(
    conn: sqlite3.Connection, *, days: float = ALERT_RETENTION_DAYS
) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = conn.execute("SELECT alert_id, alert_at FROM FCT_TRANSACTION_ALERT").fetchall()
    stale = [int(r["alert_id"]) for r in rows if parse_alert_at(r["alert_at"]) < cutoff]
    if not stale:
        return 0
    placeholders = ",".join("?" for _ in stale)
    cur = conn.execute(
        f"DELETE FROM FCT_TRANSACTION_ALERT WHERE alert_id IN ({placeholders})",
        stale,
    )
    return int(cur.rowcount)


def insert_transaction_alert(
    conn: sqlite3.Connection,
    rng: random.Random,
    *,
    alert_at: str | None = None,
) -> int | None:
    unit_count = conn.execute("SELECT COUNT(*) AS n FROM DIM_BUSINESS_UNIT").fetchone()["n"]
    if unit_count == 0:
        return None
    next_id = conn.execute(
        "SELECT COALESCE(MAX(alert_id), 0) + 1 AS n FROM FCT_TRANSACTION_ALERT"
    ).fetchone()["n"]
    unit_id = rng.randint(1, int(unit_count))
    risk = round(rng.uniform(0.42, 0.99), 2)
    status = rng.choices(
        ["New", "Under Review", "Escalated", "Cleared", "SAR Filed"],
        weights=[0.42, 0.28, 0.12, 0.14, 0.04],
    )[0]
    amount = round(rng.uniform(8_000, 3_200_000), 2)
    alert_type = rng.choice(ALERT_TYPES)
    conn.execute(
        """
        INSERT INTO FCT_TRANSACTION_ALERT
          (alert_id, unit_id, alert_at, alert_type, amount_usd, customer_ref, channel,
           status, risk_score, narrative)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            next_id,
            unit_id,
            alert_at or _utc_now_iso(),
            alert_type,
            amount,
            f"CUST-{rng.randint(10000, 99999)}",
            rng.choice(CHANNELS),
            status,
            risk,
            rng.choice(NARRATIVES),
        ),
    )
    return int(next_id)


def seconds_until_next_alert(rng: random.Random) -> float:
    """Poisson inter-arrival (mean alerts_per_day_mean() alerts per 86400s)."""
    rate_per_second = alerts_per_day_mean() / 86400.0
    return rng.expovariate(rate_per_second)


def ensure_alert_pool(
    conn: sqlite3.Connection,
    rng: random.Random,
    *,
    min_count: int = MIN_ALERT_POOL,
) -> int:
    """Keep a rolling window of recent alerts so the TM panel is never empty."""
    current = int(conn.execute("SELECT COUNT(*) AS n FROM FCT_TRANSACTION_ALERT").fetchone()["n"])
    if current >= min_count:
        return 0
    need = min_count - current
    now = datetime.now(timezone.utc)
    created = 0
    for _ in range(need):
        hours_ago = rng.uniform(0.05, 47.0)
        at = (now - timedelta(hours=hours_ago)).replace(microsecond=0).isoformat()
        if insert_transaction_alert(conn, rng, alert_at=at):
            created += 1
    return created


def run_generator_tick(conn: sqlite3.Connection, rng: random.Random) -> dict[str, Any]:
    new_id = insert_transaction_alert(conn, rng)
    return {"created_alert_id": new_id}
