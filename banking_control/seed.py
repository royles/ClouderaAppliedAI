from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from banking_control.db import apply_schema, connect, refresh_overview_cache
from banking_control.paths import default_db_path, default_schema_path

DOMAINS = [
    ("AML", "Anti-Money Laundering"),
    ("KYC", "Know Your Customer"),
    ("SOX", "Financial Reporting"),
    ("OPS", "Operational Resilience"),
    ("CYBER", "Information Security"),
    ("CREDIT", "Credit Risk"),
]

UNITS = [
    ("RB-NA", "Retail Banking — North America", "Americas"),
    ("RB-EMEA", "Retail Banking — EMEA", "EMEA"),
    ("CB-APAC", "Corporate Banking — APAC", "APAC"),
    ("WM-GLOBAL", "Wealth Management", "Global"),
    ("TS-NA", "Treasury Services", "Americas"),
]

CONTROL_TEMPLATES = [
    ("AML-001", "Large cash transaction monitoring", "AML", "Critical"),
    ("AML-002", "Sanctions screening batch reconciliation", "AML", "High"),
    ("KYC-001", "Periodic customer due diligence refresh", "KYC", "High"),
    ("KYC-002", "Beneficial ownership verification", "KYC", "Critical"),
    ("SOX-001", "Journal entry approval segregation", "SOX", "Critical"),
    ("SOX-002", "Sub-ledger to GL reconciliation", "SOX", "High"),
    ("OPS-001", "Business continuity test evidence", "OPS", "Medium"),
    ("OPS-002", "Third-party SLA attestation", "OPS", "Medium"),
    ("CYB-001", "Privileged access quarterly review", "CYBER", "Critical"),
    ("CYB-002", "Vulnerability remediation SLA tracking", "CYBER", "High"),
    ("CRD-001", "Commercial exposure limit breaches", "CREDIT", "High"),
    ("CRD-002", "Collateral revaluation cadence", "CREDIT", "Medium"),
]

STATUSES = ["Effective", "Partially Effective", "Ineffective", "Not Tested"]
EXCEPTION_STATUSES = ["Open", "In Remediation", "Pending Validation", "Closed"]
ALERT_TYPES = [
    "Structuring pattern",
    "Velocity anomaly",
    "High-risk jurisdiction",
    "Dormant account reactivation",
    "Round-dollar wire cluster",
]
CHANNELS = ["Wire", "ACH", "Branch Teller", "Mobile", "ATM"]


def _rand_date(rng: random.Random, start: date, days: int) -> str:
    return (start + timedelta(days=rng.randint(0, days))).isoformat()


def init_database(db_path: Path | None = None, *, rebuild: bool = False, seed: int = 42) -> Path:
    path = db_path or default_db_path()
    if rebuild and path.exists():
        path.unlink()

    schema = default_schema_path()
    if not schema.is_file():
        raise FileNotFoundError(
            f"Database schema not found at {schema}. "
            "Set BANKING_CONTROL_SCHEMA_PATH or BANKING_CONTROL_DATA_DIR if the repo "
            "lives in a CDSW subfolder."
        )
    conn = connect(path)
    try:
        apply_schema(conn, schema)
        if conn.execute("SELECT COUNT(*) FROM DIM_CONTROL").fetchone()[0] == 0:
            _seed(conn, seed)
        refresh_overview_cache(conn)
    finally:
        conn.close()
    return path


def _seed(conn: sqlite3.Connection, seed: int) -> None:
    rng = random.Random(seed)
    today = date.today()

    for idx, (code, name, region) in enumerate(UNITS, start=1):
        conn.execute(
            "INSERT INTO DIM_BUSINESS_UNIT (unit_id, unit_code, unit_name, region) VALUES (?, ?, ?, ?)",
            (idx, code, name, region),
        )

    for idx, (code, name, domain, tier) in enumerate(CONTROL_TEMPLATES, start=1):
        conn.execute(
            """
            INSERT INTO DIM_CONTROL
              (control_id, control_code, control_name, domain, risk_tier, owner, frequency, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                idx,
                code,
                name,
                domain,
                tier,
                f"{domain} Control Office",
                rng.choice(["Daily", "Weekly", "Monthly", "Quarterly"]),
                f"Demonstration control for {name.lower()} across retail and corporate banking lines.",
            ),
        )

    testers = ["Internal Audit", "Compliance Testing", "SOX PMO", "Model Validation"]
    for unit_id in range(1, len(UNITS) + 1):
        for control_id in range(1, len(CONTROL_TEMPLATES) + 1):
            weights = [0.72, 0.15, 0.05, 0.08]
            status = rng.choices(STATUSES, weights=weights)[0]
            conn.execute(
                """
                INSERT INTO FCT_CONTROL_ASSESSMENT
                  (assessment_id, control_id, unit_id, assessment_date, status, tester, evidence_ref, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    None,
                    control_id,
                    unit_id,
                    _rand_date(rng, today - timedelta(days=120), 90),
                    status,
                    rng.choice(testers),
                    f"EV-{control_id:03d}-{unit_id:02d}",
                    None if status == "Effective" else "Sample finding documented in workpaper.",
                ),
            )

    exception_titles = [
        "Missed sanctions rescreen within 24h SLA",
        "Dual approval bypass on high-value journal",
        "Incomplete CDD refresh for PEP segment",
        "Failed BCP failover test — RTO exceeded",
        "Privileged account not revoked after role change",
    ]
    exc_id = 1
    for _ in range(28):
        control_id = rng.randint(1, len(CONTROL_TEMPLATES))
        unit_id = rng.randint(1, len(UNITS))
        severity = rng.choice(["Critical", "High", "Medium", "Low"])
        status = rng.choices(
            EXCEPTION_STATUSES,
            weights=[0.35, 0.3, 0.15, 0.2],
        )[0]
        opened = today - timedelta(days=rng.randint(1, 90))
        due = opened + timedelta(days=rng.randint(14, 45))
        conn.execute(
            """
            INSERT INTO FCT_EXCEPTION
              (exception_id, control_id, unit_id, opened_at, severity, status, title, description,
               assignee, due_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                exc_id,
                control_id,
                unit_id,
                opened.isoformat(),
                severity,
                status,
                rng.choice(exception_titles),
                "Automated seed exception for dashboard demonstration and workflow tracking.",
                rng.choice(["jchen@bank.demo", "mrossi@bank.demo", "akim@bank.demo"]),
                due.isoformat(),
            ),
        )
        exc_id += 1

    alert_id = 1
    for _ in range(45):
        unit_id = rng.randint(1, len(UNITS))
        risk = round(rng.uniform(0.35, 0.98), 2)
        status = rng.choices(
            ["New", "Under Review", "Escalated", "Cleared", "SAR Filed"],
            weights=[0.25, 0.35, 0.15, 0.2, 0.05],
        )[0]
        amount = round(rng.uniform(5_000, 2_500_000), 2)
        conn.execute(
            """
            INSERT INTO FCT_TRANSACTION_ALERT
              (alert_id, unit_id, alert_at, alert_type, amount_usd, customer_ref, channel,
               status, risk_score, narrative)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert_id,
                unit_id,
                _rand_date(rng, today - timedelta(days=30), 29),
                rng.choice(ALERT_TYPES),
                amount,
                f"CUST-{rng.randint(10000, 99999)}",
                rng.choice(CHANNELS),
                status,
                risk,
                "Monitoring rule fired on aggregated activity; analyst review required per policy.",
            ),
        )
        alert_id += 1

    audit_actions = [
        ("Control assessment submitted", "control_assessment"),
        ("Exception status updated", "exception"),
        ("Alert escalated to AML investigations", "alert"),
        ("Evidence package uploaded", "evidence"),
    ]
    for i in range(1, 41):
        action, entity = rng.choice(audit_actions)
        conn.execute(
            """
            INSERT INTO FCT_AUDIT_EVENT
              (event_id, event_at, actor, action, entity_type, entity_id, detail)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                i,
                _rand_date(rng, today - timedelta(days=14), 13),
                rng.choice(["compliance_bot", "audit_lead", "aml_analyst", "sox_tester"]),
                action,
                entity,
                str(rng.randint(1, 50)),
                "Recorded in banking control solution audit trail.",
            ),
        )

    conn.commit()
