"""Shared WHERE clause builder for customer list / copilot queries."""

from __future__ import annotations

from customer360.api.segments import SEGMENT_WHERE, normalize_segment

VALID_CHURN_RISK_TIERS = frozenset({"HIGH", "MEDIUM", "LOW"})


KNOWN_CITIES: dict[str, str] = {
    "tel aviv": "Tel Aviv",
    "jerusalem": "Jerusalem",
    "haifa": "Haifa",
    "beer sheva": "Beer Sheva",
    "beersheba": "Beer Sheva",
    "netanya": "Netanya",
    "ashdod": "Ashdod",
    "rishon lezion": "Rishon LeZion",
    "rishon": "Rishon LeZion",
    "petah tikva": "Petah Tikva",
    "petach tikva": "Petah Tikva",
}


def normalize_city_name(raw: str | None) -> str | None:
    if not raw or not str(raw).strip():
        return None
    text = str(raw).strip()
    key = text.lower()
    if key in KNOWN_CITIES:
        return KNOWN_CITIES[key]
    for alias, canonical in KNOWN_CITIES.items():
        if alias in key or key in alias:
            return canonical
    # Title-case fallback for exact dimension match attempts
    return text if len(text) >= 2 else None


def normalize_churn_risk_tier(raw: str | None) -> str | None:
    if raw is None or not str(raw).strip():
        return None
    text = str(raw).strip().upper()
    if text in VALID_CHURN_RISK_TIERS:
        return text
    lowered = str(raw).strip().lower()
    if "high" in lowered:
        return "HIGH"
    if "medium" in lowered or "med" in lowered:
        return "MEDIUM"
    if "low" in lowered:
        return "LOW"
    return None


def customer_list_where(
    seg: str,
    q: str | None,
    policy_type_code: int | None = None,
    city: str | None = None,
    churn_risk_tier: str | None = None,
) -> tuple[str, list[object]]:
    segment_sql = SEGMENT_WHERE[normalize_segment(seg)]
    where = f"c.CURRENT_IND = 1 AND ({segment_sql})"
    params: list[object] = []
    if q and q.strip():
        where += " AND (c.CUSTOMER_NAME LIKE ? OR CAST(c.CUSTOMER_ID AS TEXT) LIKE ?)"
        like = f"%{q.strip()}%"
        params.extend([like, like])
    city_canon = normalize_city_name(city)
    if city_canon:
        where += " AND c.CITY_NAME = ?"
        params.append(city_canon)
    if policy_type_code is not None:
        where += """
            AND EXISTS (
                SELECT 1 FROM DWH_DIM_ALL_POLICY p
                WHERE p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
                  AND p.POLICY_TYPE_CODE = ?
            )
        """
        params.append(int(policy_type_code))
    tier = normalize_churn_risk_tier(churn_risk_tier)
    if tier:
        where += """
            AND EXISTS (
                SELECT 1 FROM APP_CUSTOMER_CHURN_SCORES chf
                WHERE chf.CUSTOMER_ID = c.CUSTOMER_ID
                  AND UPPER(COALESCE(chf.CHURN_RISK_TIER, '')) = ?
            )
        """
        params.append(tier)
    return where, params
