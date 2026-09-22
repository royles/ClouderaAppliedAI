"""Product catalog grouped by class for heatmap-style navigation."""

from __future__ import annotations

import sqlite3

from customer360.api.customer_list import normalize_city_name
from customer360.api.segments import SEGMENT_WHERE, normalize_segment

PRODUCT_CLASSES: list[tuple[str, str, tuple[int, ...]]] = [
    ("life_protection", "Life & protection", (101, 102)),
    ("health", "Health & supplementary", (201,)),
    ("property", "Property & elementary", (301,)),
    ("long_term_savings", "Long-term savings", (401, 402, 403)),
]


def fetch_product_catalog_city_options(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT DISTINCT c.CITY_NAME AS city_name
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        WHERE c.CURRENT_IND = 1
          AND c.CITY_NAME IS NOT NULL
          AND TRIM(c.CITY_NAME) != ''
        ORDER BY city_name ASC
        """
    ).fetchall()
    return [str(r["city_name"]) for r in rows]


def fetch_product_catalog(
    conn: sqlite3.Connection,
    *,
    segment: str | None = None,
    city: str | None = None,
) -> dict:
    seg = normalize_segment(segment)
    city_canon = normalize_city_name(city)
    customer_where = f"c.CURRENT_IND = 1 AND ({SEGMENT_WHERE[seg]})"
    params: list[object] = []
    if city_canon:
        customer_where += " AND c.CITY_NAME = ?"
        params.append(city_canon)

    rows = conn.execute(
        f"""
        SELECT
            p.POLICY_TYPE_CODE AS policy_type_code,
            MAX(p.POLICY_TYPE_DESC) AS policy_type_desc,
            COUNT(DISTINCT p.CUSTOMER_ID) AS customer_count,
            COUNT(*) AS policy_count,
            SUM(CASE WHEN p.IS_ACTIVE = 1 THEN 1 ELSE 0 END) AS active_policy_count
        FROM DWH_DIM_ALL_POLICY p
        INNER JOIN DWH_DIM_CUSTOMERS_UNIQUE c
            ON CAST(c.CUSTOMER_ID AS TEXT) = p.CUSTOMER_ID
        WHERE {customer_where}
        GROUP BY p.POLICY_TYPE_CODE
        ORDER BY customer_count DESC, policy_type_code ASC
        """,
        params,
    ).fetchall()

    by_code = {
        int(r["policy_type_code"]): {
            "policy_type_code": int(r["policy_type_code"]),
            "policy_type_desc": str(r["policy_type_desc"] or ""),
            "customer_count": int(r["customer_count"] or 0),
            "policy_count": int(r["policy_count"] or 0),
            "active_policy_count": int(r["active_policy_count"] or 0),
        }
        for r in rows
    }

    max_customers = max((p["customer_count"] for p in by_code.values()), default=0)

    classes: list[dict] = []
    for class_key, class_label, codes in PRODUCT_CLASSES:
        products = [by_code[c] for c in codes if c in by_code]
        customer_total = sum(p["customer_count"] for p in products)
        classes.append(
            {
                "class_key": class_key,
                "class_label": class_label,
                "customer_count": customer_total,
                "policy_count": sum(p["policy_count"] for p in products),
                "products": products,
            }
        )

    return {
        "max_customer_count": max_customers,
        "classes": classes,
        "filters": {
            "segment": seg,
            "city": city_canon,
        },
        "city_options": fetch_product_catalog_city_options(conn),
    }
