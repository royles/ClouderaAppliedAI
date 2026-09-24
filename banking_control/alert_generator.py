from __future__ import annotations

import random
import sqlite3
from datetime import datetime, timedelta, timezone
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

# ~100 TM alerts / day ≈ mid-size EU retail + commercial bank operating volume.
ALERTS_PER_DAY_MEAN = 100.0

NARRATIVES: tuple[str, ...] = (
    "Monitoring rule fired on aggregated activity; analyst review required per policy.",
    "Scenario exceeded velocity threshold versus 30-day customer baseline.",
    "Counterparty jurisdiction flagged on internal high-risk corridor list.",
    "Multiple round-dollar credits followed by immediate outbound wires.",
    "Instant payment burst inconsistent with declared account purpose.",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def expire_alerts_older_than(conn: sqlite3.Connection, *, days: float = 2.0) -> int:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).replace(microsecond=0)
    cutoff_s = cutoff.isoformat()
    cur = conn.execute(
        "DELETE FROM FCT_TRANSACTION_ALERT WHERE alert_at < ?",
        (cutoff_s,),
    )
    return int(cur.rowcount)


def insert_transaction_alert(conn: sqlite3.Connection, rng: random.Random) -> int | None:
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
            _utc_now_iso(),
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
    """Poisson process inter-arrival (mean ALERTS_PER_DAY_MEAN alerts per 86400s)."""
    rate_per_second = ALERTS_PER_DAY_MEAN / 86400.0
    return rng.expovariate(rate_per_second)


def run_generator_tick(conn: sqlite3.Connection, rng: random.Random) -> dict[str, Any]:
    expired = expire_alerts_older_than(conn, days=2.0)
    new_id = insert_transaction_alert(conn, rng)
    return {"expired": expired, "created_alert_id": new_id}
