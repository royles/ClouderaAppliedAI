"""Build normalized feature matrix and churn labels from the warehouse."""

from __future__ import annotations

import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd

from customer360.interactions.summary import REFERENCE_DATE, interactions_table_exists

FEATURE_COLUMNS = [
    "policy_count",
    "active_policy_count",
    "inactive_policy_count",
    "total_monthly_premium",
    "avg_policy_status_code",
    "investment_track_count",
    "total_accumulation",
    "has_foreclosure",
    "foreclosure_amount",
    "days_since_last_login",
    "portal_registered",
    "communication_code",
    "smoker_flag",
    "customer_age_years",
    "collective_policy_count",
    "interaction_count_90d",
    "review_count_90d",
    "review_avg_rating_90d",
    "negative_review_count_90d",
    "agent_question_count_90d",
    "unresolved_agent_questions_90d",
    "web_search_count_90d",
    "help_search_count_90d",
    "days_since_last_interaction",
]

INTERACTION_FEATURE_COLUMNS = [
    "interaction_count_90d",
    "review_count_90d",
    "review_avg_rating_90d",
    "negative_review_count_90d",
    "agent_question_count_90d",
    "unresolved_agent_questions_90d",
    "web_search_count_90d",
    "help_search_count_90d",
    "days_since_last_interaction",
]


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        if " " in value:
            return datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S")
        return datetime.strptime(value[:10], "%Y-%m-%d")
    except ValueError:
        return None


def load_customer_frame(conn: sqlite3.Connection) -> pd.DataFrame:
    sql = """
    SELECT
        c.CUSTOMER_ID AS customer_id,
        c.LAST_LOGIN AS last_login,
        c.USER_SITE_REGISTER_STATUS AS portal_registered,
        c.COMMUNICATION_CODE AS communication_code,
        c.SMOKER_STATUS_CODE AS smoker_status_code,
        c.BIRTH_DATE AS birth_date,
        (
            SELECT COUNT(*)
            FROM DWH_DIM_ALL_POLICY p
            WHERE p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
        ) AS policy_count,
        (
            SELECT COUNT(*)
            FROM DWH_DIM_ALL_POLICY p
            WHERE p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT) AND p.IS_ACTIVE = 1
        ) AS active_policy_count,
        (
            SELECT COUNT(*)
            FROM DWH_DIM_ALL_POLICY p
            WHERE p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT) AND p.IS_ACTIVE = 0
        ) AS inactive_policy_count,
        (
            SELECT COALESCE(SUM(p.BRUTO_MONTHLY_PREMIUM), 0)
            FROM DWH_DIM_ALL_POLICY p
            WHERE p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT) AND p.IS_ACTIVE = 1
        ) AS total_monthly_premium,
        (
            SELECT COALESCE(AVG(p.POLICY_STATUS_CODE), 0)
            FROM DWH_DIM_ALL_POLICY p
            WHERE p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
        ) AS avg_policy_status_code,
        (
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT pit.POLICY_NUM, pit.INVESTMENT_TRACK_ID
                FROM DWH_FCT_POLICY_INVESTMENT_TRACK pit
                WHERE pit.CUSTOMER_ID = c.CUSTOMER_ID
            )
        ) AS investment_track_count,
        (
            SELECT COALESCE(SUM(latest.ACCUMULATION_TOTAL), 0)
            FROM (
                SELECT pit.ACCUMULATION_TOTAL,
                       ROW_NUMBER() OVER (
                           PARTITION BY pit.POLICY_NUM, pit.INVESTMENT_TRACK_ID
                           ORDER BY pit.SNAPSHOT_DATE DESC
                       ) AS rn
                FROM DWH_FCT_POLICY_INVESTMENT_TRACK pit
                WHERE pit.CUSTOMER_ID = c.CUSTOMER_ID
            ) latest
            WHERE latest.rn = 1
        ) AS total_accumulation,
        (
            SELECT COUNT(*)
            FROM DWH_FCT_FORECLOSURES f
            WHERE f.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
        ) AS foreclosure_count,
        (
            SELECT COALESCE(SUM(f.FORECLOSURES_AMOUNT), 0)
            FROM DWH_FCT_FORECLOSURES f
            WHERE f.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
        ) AS foreclosure_amount,
        (
            SELECT COUNT(*)
            FROM DWH_DIM_ALL_POLICY p
            WHERE p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT) AND p.IS_COLECTIVE = 1
        ) AS collective_policy_count
    FROM DWH_DIM_CUSTOMERS_UNIQUE c
    WHERE c.CURRENT_IND = 1
    """
    df = pd.read_sql_query(sql, conn)
    df["has_foreclosure"] = (df["foreclosure_count"] > 0).astype(int)
    df.drop(columns=["foreclosure_count"], inplace=True)

    days: list[float] = []
    ages: list[float] = []
    for _, row in df.iterrows():
        login_dt = _parse_date(row["last_login"])
        if login_dt:
            days.append(max(0.0, (REFERENCE_DATE - login_dt).days))
        else:
            days.append(999.0)
        birth_dt = _parse_date(row["birth_date"])
        if birth_dt:
            ages.append(max(18.0, (REFERENCE_DATE - birth_dt).days / 365.25))
        else:
            ages.append(45.0)
    df["days_since_last_login"] = days
    df["customer_age_years"] = ages
    df["portal_registered"] = df["portal_registered"].fillna(0).astype(int)
    df["communication_code"] = df["communication_code"].fillna(0).astype(float)
    df["smoker_flag"] = (df["smoker_status_code"].astype(str) == "1").astype(int)
    df.drop(columns=["smoker_status_code", "birth_date", "last_login"], inplace=True)

    df = _append_interaction_features(conn, df)

    for col in FEATURE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df


def _append_interaction_features(conn: sqlite3.Connection, df: pd.DataFrame) -> pd.DataFrame:
    if not interactions_table_exists(conn):
        for col in INTERACTION_FEATURE_COLUMNS:
            df[col] = 999.0 if col == "days_since_last_interaction" else 0.0
        return df

    ref = REFERENCE_DATE.strftime("%Y-%m-%d")
    interaction_df = pd.read_sql_query(
        f"""
        SELECT
            CUSTOMER_ID AS customer_id,
            SUM(CASE WHEN julianday('{ref}') - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                AS interaction_count_90d,
            SUM(CASE WHEN EVENT_TYPE = 'REVIEW'
                AND julianday('{ref}') - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                AS review_count_90d,
            AVG(CASE WHEN EVENT_TYPE = 'REVIEW'
                AND julianday('{ref}') - julianday(EVENT_TS) <= 90 THEN RATING END)
                AS review_avg_rating_90d,
            SUM(CASE WHEN EVENT_TYPE = 'REVIEW' AND RATING <= 2
                AND julianday('{ref}') - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                AS negative_review_count_90d,
            SUM(CASE WHEN EVENT_TYPE = 'AGENT_QUESTION'
                AND julianday('{ref}') - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                AS agent_question_count_90d,
            SUM(CASE WHEN EVENT_TYPE = 'AGENT_QUESTION' AND COALESCE(RESOLVED, 1) = 0
                AND julianday('{ref}') - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                AS unresolved_agent_questions_90d,
            SUM(CASE WHEN EVENT_TYPE = 'WEB_SEARCH'
                AND julianday('{ref}') - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                AS web_search_count_90d,
            SUM(CASE WHEN EVENT_TYPE = 'WEB_SEARCH' AND TOPIC = 'help_center'
                AND julianday('{ref}') - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                AS help_search_count_90d,
            MIN(julianday('{ref}') - julianday(EVENT_TS)) AS days_since_last_interaction
        FROM APP_CUSTOMER_INTERACTION_EVENTS
        GROUP BY CUSTOMER_ID
        """,
        conn,
    )
    df = df.merge(interaction_df, on="customer_id", how="left")
    df["review_avg_rating_90d"] = df["review_avg_rating_90d"].fillna(0.0)
    df["days_since_last_interaction"] = df["days_since_last_interaction"].fillna(999.0)
    for col in (
        "interaction_count_90d",
        "review_count_90d",
        "negative_review_count_90d",
        "agent_question_count_90d",
        "unresolved_agent_questions_90d",
        "web_search_count_90d",
        "help_search_count_90d",
    ):
        df[col] = df[col].fillna(0.0)
    return df


def derive_churn_label(df: pd.DataFrame) -> pd.Series:
    """
    Observed churn proxy — tuned for ~10–18% positive rate on synthetic book:
    strong lapse / disengagement signals, not single weak touchpoints.
    """
    no_active = df["active_policy_count"] <= 0
    dormant_portal = (df["portal_registered"] == 1) & (df["days_since_last_login"] >= 150)
    mostly_lapsed = (df["policy_count"] > 0) & (
        df["inactive_policy_count"] >= df["active_policy_count"]
    ) & (df["avg_policy_status_code"] >= 50)
    disengaged = (df["days_since_last_interaction"] >= 150) & (
        df["interaction_count_90d"] <= 1
    )
    unhappy_reviews = (df["review_count_90d"] >= 2) & (df["review_avg_rating_90d"] <= 2.2)
    open_agent_cases = df["unresolved_agent_questions_90d"] >= 2
    help_stress = (df["help_search_count_90d"] >= 3) & (
        df["help_search_count_90d"] >= df["web_search_count_90d"] * 0.6
    )
    foreclosure_stress = (df["has_foreclosure"] == 1) & (
        no_active | dormant_portal | (df["days_since_last_interaction"] >= 120)
    )
    churn = (
        no_active
        | mostly_lapsed
        | (dormant_portal & disengaged)
        | (unhappy_reviews & open_agent_cases)
        | (help_stress & disengaged)
        | foreclosure_stress
    ).astype(int)
    return churn


def feature_matrix(df: pd.DataFrame) -> np.ndarray:
    return df[FEATURE_COLUMNS].to_numpy(dtype=np.float64)
