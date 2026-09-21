"""Customer list segments tied to overview cards."""

from __future__ import annotations

from typing import Literal

SegmentKey = Literal[
    "customers_all",
    "with_policies",
    "with_foreclosures",
    "with_investments",
    "with_insurance_status",
    "with_market_products",
]

OVERVIEW_DOMAINS: list[tuple[str, str, str, str]] = [
    (
        "Customers (current)",
        "customers_all",
        "All active customer dimension rows",
        "SELECT COUNT(*) FROM DWH_DIM_CUSTOMERS_UNIQUE WHERE CURRENT_IND = 1",
    ),
    (
        "Policies",
        "with_policies",
        "Customers with at least one policy",
        """
        SELECT COUNT(DISTINCT c.CUSTOMER_ID)
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        INNER JOIN DWH_DIM_ALL_POLICY p ON p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
        WHERE c.CURRENT_IND = 1
        """,
    ),
    (
        "Foreclosures",
        "with_foreclosures",
        "Customers with legal encumbrance records",
        """
        SELECT COUNT(DISTINCT c.CUSTOMER_ID)
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        INNER JOIN DWH_FCT_FORECLOSURES f ON f.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
        WHERE c.CURRENT_IND = 1
        """,
    ),
    (
        "Policy investment snapshots",
        "with_investments",
        "Customers with policy investment track balances",
        """
        SELECT COUNT(DISTINCT c.CUSTOMER_KEY)
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        INNER JOIN DWH_FCT_POLICY_INVESTMENT_TRACK pit ON pit.CUSTOMER_ID = c.CUSTOMER_ID
        WHERE c.CURRENT_IND = 1
        """,
    ),
    (
        "Market tracks",
        "with_market_products",
        "Customers with pension / gemel / life investment products",
        """
        SELECT COUNT(DISTINCT c.CUSTOMER_ID)
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        INNER JOIN DWH_DIM_ALL_POLICY p ON p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
        WHERE c.CURRENT_IND = 1
          AND p.MNG_COMPANY_CODE IN (1, 7, 8)
          AND p.IS_ACTIVE = 1
        """,
    ),
    (
        "Insurance status rows",
        "with_insurance_status",
        "Customers with matzav bituach coverage snapshots",
        """
        SELECT COUNT(DISTINCT c.CUSTOMER_KEY)
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        INNER JOIN FCT_MATZAV_BITUACH m ON m.MS_MEVUTACH = c.CUSTOMER_ID
        WHERE c.CURRENT_IND = 1
        """,
    ),
]

SEGMENT_WHERE: dict[str, str] = {
    "customers_all": "1=1",
    "with_policies": """
        EXISTS (
            SELECT 1 FROM DWH_DIM_ALL_POLICY p2
            WHERE p2.CUSTOMER_KEY = c.CUSTOMER_KEY
        )
    """,
    "with_foreclosures": """
        EXISTS (
            SELECT 1 FROM DWH_FCT_FORECLOSURES f
            WHERE f.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
        )
    """,
    "with_investments": """
        EXISTS (
            SELECT 1 FROM DWH_FCT_POLICY_INVESTMENT_TRACK pit
            WHERE pit.CUSTOMER_ID = c.CUSTOMER_ID
        )
    """,
    "with_market_products": """
        EXISTS (
            SELECT 1 FROM DWH_DIM_ALL_POLICY p2
            WHERE p2.CUSTOMER_KEY = c.CUSTOMER_KEY
              AND p2.MNG_COMPANY_CODE IN (1, 7, 8)
              AND p2.IS_ACTIVE = 1
        )
    """,
    "with_insurance_status": """
        EXISTS (
            SELECT 1 FROM FCT_MATZAV_BITUACH m
            WHERE m.MS_MEVUTACH = c.CUSTOMER_ID
        )
    """,
}


def normalize_segment(segment: str | None) -> str:
    key = (segment or "customers_all").strip()
    if key not in SEGMENT_WHERE:
        return "customers_all"
    return key
