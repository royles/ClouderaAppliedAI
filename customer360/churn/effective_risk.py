"""Map churn tiers and ML scores to a single 12-month lapse probability."""

from __future__ import annotations

# Tier anchors when CHURN_PROBABILITY is missing or zero (book-weighted in KPIs).
TIER_CHURN_RATE: dict[str, float] = {
    "LOW": 0.05,
    "MEDIUM": 0.15,
    "HIGH": 0.40,
}

BOOK_DEFAULT_CHURN_RATE = 0.12


def normalize_tier(tier: str | None) -> str | None:
    if not tier:
        return None
    key = tier.strip().upper()
    if key in TIER_CHURN_RATE:
        return key
    return None


def tier_churn_rate(tier: str | None) -> float:
    normalized = normalize_tier(tier)
    if normalized:
        return TIER_CHURN_RATE[normalized]
    return TIER_CHURN_RATE["LOW"]


def effective_churn_probability(
    probability: float | None,
    tier: str | None,
    *,
    scored: bool = True,
) -> float:
    """Estimated 12-month lapse probability for one customer."""
    if not scored:
        return 0.0
    if probability is not None and probability > 0:
        return float(probability)
    return tier_churn_rate(tier)


def effective_churn_probability_sql(ch_alias: str = "ch") -> str:
    """SQL expression (requires LEFT JOIN on APP_CUSTOMER_CHURN_SCORES AS ch)."""
    high = TIER_CHURN_RATE["HIGH"]
    medium = TIER_CHURN_RATE["MEDIUM"]
    low = TIER_CHURN_RATE["LOW"]
    return f"""
    CASE
        WHEN {ch_alias}.CUSTOMER_ID IS NULL THEN 0
        ELSE COALESCE(
            NULLIF({ch_alias}.CHURN_PROBABILITY, 0),
            CASE UPPER(COALESCE({ch_alias}.CHURN_RISK_TIER, ''))
                WHEN 'HIGH' THEN {high}
                WHEN 'MEDIUM' THEN {medium}
                WHEN 'LOW' THEN {low}
                ELSE {low}
            END
        )
    END
    """.strip()
