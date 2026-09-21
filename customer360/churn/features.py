"""Build normalized feature matrix and churn labels from the warehouse."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

REFERENCE_DATE = datetime(2025, 9, 15)

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

    for col in FEATURE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df


def derive_churn_label(df: pd.DataFrame) -> pd.Series:
    """
    Observed churn proxy from warehouse behaviour:
    - no active policies, or
    - portal user with no login in 90+ days, or
    - majority of policies lapsed / surrendered (avg status >= 55)
    """
    no_active = df["active_policy_count"] <= 0
    dormant_portal = (df["portal_registered"] == 1) & (df["days_since_last_login"] >= 90)
    bad_status = (df["policy_count"] > 0) & (df["avg_policy_status_code"] >= 55)
    churn = (no_active | dormant_portal | bad_status).astype(int)
    return churn


def feature_matrix(df: pd.DataFrame) -> np.ndarray:
    return df[FEATURE_COLUMNS].to_numpy(dtype=np.float64)
