"""Customer 360 REST API routes."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from customer360.api.deps import get_db
from customer360.api.schemas import (
    CustomerDetailResponse,
    CustomerProfile,
    CustomerSummary,
    DomainCount,
    ForeclosureRow,
    HealthResponse,
    InvestmentSnapshot,
    OverviewResponse,
    PolicyRow,
)
from customer360.api.segments import OVERVIEW_DOMAINS, SEGMENT_WHERE, normalize_segment
from customer360.api.sorting import normalize_sort_by, normalize_sort_order, order_clause
from customer360.paths import default_db_path

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/overview", response_model=OverviewResponse)
def overview(conn: Annotated[sqlite3.Connection, Depends(get_db)]) -> OverviewResponse:
    domains: list[DomainCount] = []
    for label, filter_key, description, count_sql in OVERVIEW_DOMAINS:
        row_count = conn.execute(count_sql).fetchone()[0]
        domains.append(
            DomainCount(
                domain=label,
                row_count=row_count,
                filter_key=filter_key,
                description=description,
            )
        )
    return OverviewResponse(
        domains=domains,
        database_path=str(default_db_path()),
    )


@router.get("/customers", response_model=list[CustomerSummary])
def list_customers(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    q: str | None = Query(None, description="Search name or customer ID"),
    segment: str | None = Query(
        None,
        description="Overview card filter key (e.g. with_policies, with_foreclosures)",
    ),
    sort_by: str | None = Query(
        None,
        description="Sort key: name, policy_count, or investment_count",
    ),
    sort_order: str | None = Query(
        None,
        description="Sort direction: asc or desc (defaults: desc for counts, asc for name)",
    ),
    limit: int = Query(50, ge=1, le=200),
) -> list[CustomerSummary]:
    seg = normalize_segment(segment)
    segment_sql = SEGMENT_WHERE[seg]
    sort_key = normalize_sort_by(sort_by)
    order_key = normalize_sort_order(sort_order, sort_by=sort_key)

    sql = f"""
        SELECT
            c.CUSTOMER_ID AS customer_id,
            c.CUSTOMER_KEY AS customer_key,
            c.CUSTOMER_NAME AS customer_name,
            c.CITY_NAME AS city_name,
            c.EMAIL AS email,
            c.MOBILE_NO AS mobile_no,
            c.LAST_LOGIN AS last_login,
            (
                SELECT COUNT(*)
                FROM DWH_DIM_ALL_POLICY p
                WHERE p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
            ) AS policy_count,
            (
                SELECT COUNT(*)
                FROM (
                    SELECT DISTINCT pit.POLICY_NUM, pit.INVESTMENT_TRACK_ID
                    FROM DWH_FCT_POLICY_INVESTMENT_TRACK pit
                    WHERE pit.CUSTOMER_ID = c.CUSTOMER_ID
                )
            ) AS investment_count
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        WHERE c.CURRENT_IND = 1 AND ({segment_sql})
    """
    params: list[object] = []
    if q and q.strip():
        sql += " AND (c.CUSTOMER_NAME LIKE ? OR CAST(c.CUSTOMER_ID AS TEXT) LIKE ?)"
        like = f"%{q.strip()}%"
        params.extend([like, like])
    sql += f" ORDER BY {order_clause(sort_key, order_key)} LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [CustomerSummary(**dict(r)) for r in rows]


@router.get("/customers/{customer_id}", response_model=CustomerDetailResponse)
def customer_detail(
    customer_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> CustomerDetailResponse:
    profile_row = conn.execute(
        """
        SELECT
            CUSTOMER_ID AS customer_id,
            CUSTOMER_KEY AS customer_key,
            CUSTOMER_NAME AS customer_name,
            CUSTOMER_TYPE_DSC AS customer_type_dsc,
            BIRTH_DATE AS birth_date,
            MARITAL_STATUS_DSC AS marital_status_dsc,
            EMAIL AS email,
            MOBILE_NO AS mobile_no,
            CITY_NAME AS city_name,
            STREET_NAME AS street_name,
            COMMUNICATION_DSC AS communication_dsc,
            LAST_LOGIN AS last_login
        FROM DWH_DIM_CUSTOMERS_UNIQUE
        WHERE CURRENT_IND = 1 AND CUSTOMER_ID = ?
        """,
        (customer_id,),
    ).fetchone()
    if profile_row is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    policies = conn.execute(
        """
        SELECT
            POLICY_NUM AS policy_num,
            POLICY_TYPE_DESC AS policy_type_desc,
            IS_ACTIVE AS is_active,
            POLICY_STATUS_DESC AS policy_status_desc,
            BRUTO_MONTHLY_PREMIUM AS bruto_monthly_premium,
            POLICY_START_DATE AS policy_start_date
        FROM DWH_DIM_ALL_POLICY
        WHERE CUSTOMER_ID = ?
        ORDER BY IS_ACTIVE DESC, POLICY_NUM
        """,
        (str(customer_id),),
    ).fetchall()

    foreclosures = conn.execute(
        """
        SELECT
            FORECLOSURES_NUMBER AS foreclosures_number,
            FORECLOSURES_AMOUNT AS foreclosures_amount,
            FORECLOSURES_DATE AS foreclosures_date,
            PORTFOLIO_NUMBER AS portfolio_number
        FROM DWH_FCT_FORECLOSURES
        WHERE CUSTOMER_ID = ?
        ORDER BY FORECLOSURES_DATE DESC
        """,
        (str(customer_id),),
    ).fetchall()

    investments = conn.execute(
        """
        SELECT
            policy_num,
            snapshot_date,
            accumulation_total,
            yearly_profit_loss_total,
            fund_id
        FROM (
            SELECT
                POLICY_NUM AS policy_num,
                SNAPSHOT_DATE AS snapshot_date,
                ACCUMULATION_TOTAL AS accumulation_total,
                YEARLY_PROFIT_LOSS_TOTAL AS yearly_profit_loss_total,
                FUND_ID AS fund_id,
                ROW_NUMBER() OVER (
                    PARTITION BY POLICY_NUM, INVESTMENT_TRACK_ID
                    ORDER BY SNAPSHOT_DATE DESC
                ) AS rn
            FROM DWH_FCT_POLICY_INVESTMENT_TRACK
            WHERE CUSTOMER_ID = ?
        ) t
        WHERE rn = 1
        ORDER BY policy_num, fund_id
        LIMIT 20
        """,
        (customer_id,),
    ).fetchall()

    return CustomerDetailResponse(
        profile=CustomerProfile(**dict(profile_row)),
        policies=[PolicyRow(**dict(r)) for r in policies],
        foreclosures=[ForeclosureRow(**dict(r)) for r in foreclosures],
        investments=[InvestmentSnapshot(**dict(r)) for r in investments],
    )
