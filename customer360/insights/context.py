"""Build anonymized customer context for insight prompts."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass

from customer360.interactions.summary import load_interaction_bundle

@dataclass
class CustomerContext:
    customer_id: int
    payload: dict
    context_hash: str
    churn_tier: str | None
    churn_probability: float | None


def _active_policy_summary(policies: list[sqlite3.Row]) -> dict:
    active = [p for p in policies if p["is_active"]]
    types = sorted({p["policy_type_desc"] for p in active if p["policy_type_desc"]})
    premium = sum(p["bruto_monthly_premium"] or 0 for p in active)
    return {
        "total_policies": len(policies),
        "active_policies": len(active),
        "active_policy_types": types[:8],
        "total_monthly_premium_ils": round(premium, 2),
    }


def _investment_summary(investments: list[sqlite3.Row]) -> dict:
    accumulation = sum(i["accumulation_total"] or 0 for i in investments)
    ytd = sum(i["yearly_profit_loss_total"] or 0 for i in investments)
    return {
        "snapshot_count": len(investments),
        "total_accumulation_ils": round(accumulation, 2),
        "total_ytd_pl_ils": round(ytd, 2),
    }


def _fetch_churn(conn: sqlite3.Connection, customer_id: int) -> tuple[str | None, float | None]:
    row = conn.execute(
        """
        SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_CUSTOMER_CHURN_SCORES'
        """
    ).fetchone()
    if row is None:
        return None, None
    churn_row = conn.execute(
        """
        SELECT CHURN_PROBABILITY, CHURN_RISK_TIER
        FROM APP_CUSTOMER_CHURN_SCORES
        WHERE CUSTOMER_ID = ?
        """,
        (customer_id,),
    ).fetchone()
    if churn_row is None:
        return None, None
    return churn_row["CHURN_RISK_TIER"], churn_row["CHURN_PROBABILITY"]


def load_customer_context(conn: sqlite3.Connection, customer_id: int) -> CustomerContext | None:
    profile_row = conn.execute(
        """
        SELECT
            CUSTOMER_ID AS customer_id,
            CUSTOMER_NAME AS customer_name,
            CUSTOMER_TYPE_DSC AS customer_type_dsc,
            MARITAL_STATUS_DSC AS marital_status_dsc,
            CITY_NAME AS city_name,
            COMMUNICATION_DSC AS communication_dsc,
            LAST_LOGIN AS last_login
        FROM DWH_DIM_CUSTOMERS_UNIQUE
        WHERE CURRENT_IND = 1 AND CUSTOMER_ID = ?
        """,
        (customer_id,),
    ).fetchone()
    if profile_row is None:
        return None

    policies = conn.execute(
        """
        SELECT
            POLICY_TYPE_DESC AS policy_type_desc,
            IS_ACTIVE AS is_active,
            POLICY_STATUS_DESC AS policy_status_desc,
            BRUTO_MONTHLY_PREMIUM AS bruto_monthly_premium
        FROM DWH_DIM_ALL_POLICY
        WHERE CUSTOMER_ID = ?
        """,
        (str(customer_id),),
    ).fetchall()

    foreclosures = conn.execute(
        """
        SELECT COUNT(*) AS cnt, COALESCE(SUM(FORECLOSURES_AMOUNT), 0) AS total_amount
        FROM DWH_FCT_FORECLOSURES
        WHERE CUSTOMER_ID = ?
        """,
        (str(customer_id),),
    ).fetchone()

    investments = conn.execute(
        """
        SELECT
            accumulation_total,
            yearly_profit_loss_total
        FROM (
            SELECT
                ACCUMULATION_TOTAL AS accumulation_total,
                YEARLY_PROFIT_LOSS_TOTAL AS yearly_profit_loss_total,
                ROW_NUMBER() OVER (
                    PARTITION BY POLICY_NUM, INVESTMENT_TRACK_ID
                    ORDER BY SNAPSHOT_DATE DESC
                ) AS rn
            FROM DWH_FCT_POLICY_INVESTMENT_TRACK
            WHERE CUSTOMER_ID = ?
        ) t
        WHERE rn = 1
        LIMIT 20
        """,
        (customer_id,),
    ).fetchall()

    churn_tier, churn_prob = _fetch_churn(conn, customer_id)
    interaction_bundle = load_interaction_bundle(conn, customer_id, limit=12)

    payload = {
        "customer_id": profile_row["customer_id"],
        "customer_name": profile_row["customer_name"],
        "customer_type": profile_row["customer_type_dsc"],
        "marital_status": profile_row["marital_status_dsc"],
        "city": profile_row["city_name"],
        "preferred_communication": profile_row["communication_dsc"],
        "last_login": profile_row["last_login"],
        "policies": _active_policy_summary(policies),
        "foreclosures": {
            "count": int(foreclosures["cnt"]),
            "total_amount_ils": round(float(foreclosures["total_amount"] or 0), 2),
        },
        "investments": _investment_summary(investments),
        "churn": {
            "risk_tier": churn_tier,
            "probability": churn_prob,
        },
        "interactions": interaction_bundle["summary"],
        "recent_interactions": interaction_bundle["summary"].get("recent_highlights", []),
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    context_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return CustomerContext(
        customer_id=customer_id,
        payload=payload,
        context_hash=context_hash,
        churn_tier=churn_tier,
        churn_probability=churn_prob,
    )
