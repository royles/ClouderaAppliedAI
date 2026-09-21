"""Generate synthetic interaction events aligned with customer risk profiles."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

REFERENCE = datetime(2025, 9, 15, 12, 0, 0)

PRODUCT_SEARCHES = [
    "Compare pension balanced vs equity tracks",
    "Critical illness rider eligibility",
    "Add family member to health supplementary",
    "Study fund contribution limits",
    "Life insurance coverage calculator",
    "Property policy renewal quote",
]

HELP_SEARCHES = [
    "How to update payment method",
    "Cancel or surrender a policy",
    "Missing premium payment options",
    "Portal login verification code",
    "Download annual policy statement",
    "Complaint escalation process",
    "Change communication preferences",
]

AGENT_TOPICS = [
    ("Premium increase explanation", "billing", True),
    ("Switch investment track on pension", "investments", True),
    ("Request policy cancellation", "retention", False),
    ("Coverage gap after job change", "coverage", True),
    ("Foreclosure impact on policies", "legal", False),
    ("Claim status follow-up", "claims", True),
    ("Duplicate charge on credit card", "billing", False),
]

REVIEW_TITLES = [
    "Mobile app experience",
    "Claims handling speed",
    "Agent courtesy on phone",
    "Pension statement clarity",
    "Health plan network",
    "Digital self-service tools",
]


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _customer_policy_stats(policies: list[dict], customer_id: int) -> tuple[int, int, float]:
    cust_policies = [p for p in policies if p["CUSTOMER_ID"] == str(customer_id)]
    total = len(cust_policies)
    active = sum(1 for p in cust_policies if p["IS_ACTIVE"])
    inactive_ratio = (total - active) / total if total else 1.0
    return total, active, inactive_ratio


def _segment_risk_weight(segment: str | None) -> float:
    if segment == "at_risk":
        return 0.82
    if segment == "stable":
        return 0.48
    return 0.18


def _risk_weight(
    customer: dict,
    policies: list[dict],
    foreclosure_ids: set[int],
) -> float:
    """0 = engaged/low stress, 1 = disengaged/high stress."""
    segment = customer.get("_segment")
    if segment:
        weight = _segment_risk_weight(segment)
    else:
        weight = 0.35

    cid = int(customer["CUSTOMER_ID"])
    _, active, inactive_ratio = _customer_policy_stats(policies, cid)

    if customer.get("USER_SITE_REGISTER_STATUS") != 1:
        weight += 0.08
    last_login = customer.get("LAST_LOGIN")
    if not last_login:
        weight += 0.1
    elif isinstance(last_login, str):
        try:
            login_dt = datetime.strptime(last_login[:19], "%Y-%m-%d %H:%M:%S")
            days = (REFERENCE - login_dt).days
            if days > 120:
                weight += 0.2
            elif days > 60:
                weight += 0.08
        except ValueError:
            weight += 0.05

    if active <= 0:
        weight += 0.25
    weight += inactive_ratio * 0.12

    if cid in foreclosure_ids:
        weight += 0.15

    return min(1.0, max(0.0, weight))


def build_interaction_events(
    customers: list[dict],
    policies: list[dict],
    foreclosure_rows: list[dict],
    *,
    rng: random.Random | None = None,
) -> list[dict]:
    rng = rng or random.Random(36085)
    foreclosure_ids = {int(row["CUSTOMER_ID"]) for row in foreclosure_rows}
    rows: list[dict] = []
    event_id = 0

    active_customers = [c for c in customers if c.get("CURRENT_IND") == 1]

    for customer in active_customers:
        cid = int(customer["CUSTOMER_ID"])
        segment = customer.get("_segment", "engaged")
        risk = _risk_weight(customer, policies, foreclosure_ids)

        if segment == "engaged":
            base_events = rng.randint(14, 28)
            recent_bias = 0.85
        elif segment == "stable":
            base_events = rng.randint(10, 20)
            recent_bias = 0.55
        else:
            base_events = rng.randint(6, 14)
            recent_bias = 0.25

        for _ in range(base_events):
            event_id += 1
            if rng.random() < recent_bias:
                days_ago = rng.randint(1, 45)
            else:
                days_ago = rng.randint(46, 150)
            event_ts = REFERENCE - timedelta(days=days_ago, hours=rng.randint(0, 10))

            roll = rng.random()
            if roll < 0.18:
                event_type = "REVIEW"
                title = rng.choice(REVIEW_TITLES)
                if risk > 0.55:
                    rating = rng.choices([1, 2, 3, 4], weights=[25, 25, 30, 20])[0]
                elif risk < 0.35:
                    rating = rng.choices([3, 4, 5], weights=[10, 35, 55])[0]
                else:
                    rating = rng.choices([2, 3, 4, 5], weights=[10, 25, 40, 25])[0]
                sentiment = round((rating - 3) / 2 + rng.uniform(-0.2, 0.2), 2)
                channel = rng.choice(["web", "app", "email_survey"])
                detail = (
                    "Praised quick resolution." if rating >= 4 else "Requested clearer follow-up."
                )
                rows.append(
                    {
                        "EVENT_ID": event_id,
                        "CUSTOMER_ID": cid,
                        "EVENT_TYPE": event_type,
                        "EVENT_TS": _iso(event_ts),
                        "CHANNEL": channel,
                        "TOPIC": "service_quality",
                        "QUERY_OR_TITLE": title,
                        "RATING": rating,
                        "SENTIMENT": sentiment,
                        "RESOLVED": None,
                        "DETAIL": detail,
                    }
                )
            elif roll < 0.48:
                event_type = "AGENT_QUESTION"
                title, topic, default_resolved = rng.choice(AGENT_TOPICS)
                if risk > 0.6 and topic in ("retention", "legal", "billing"):
                    resolved = 0 if rng.random() < 0.45 else 1
                else:
                    resolved = 1 if (default_resolved and rng.random() < 0.9) else 0
                channel = rng.choice(["phone", "chat", "branch"])
                detail = "Agent provided next steps." if resolved else "Customer awaiting callback."
                rows.append(
                    {
                        "EVENT_ID": event_id,
                        "CUSTOMER_ID": cid,
                        "EVENT_TYPE": event_type,
                        "EVENT_TS": _iso(event_ts),
                        "CHANNEL": channel,
                        "TOPIC": topic,
                        "QUERY_OR_TITLE": title,
                        "RATING": None,
                        "SENTIMENT": round(rng.uniform(-0.6, 0.3) if not resolved else rng.uniform(0, 0.7), 2),
                        "RESOLVED": resolved,
                        "DETAIL": detail,
                    }
                )
            else:
                event_type = "WEB_SEARCH"
                help_bias = 0.08 + risk * 0.35
                is_help = rng.random() < help_bias
                if is_help:
                    query = rng.choice(HELP_SEARCHES)
                    topic = "help_center"
                else:
                    query = rng.choice(PRODUCT_SEARCHES)
                    topic = "product_exploration"
                channel = rng.choice(["web", "app"])
                rows.append(
                    {
                        "EVENT_ID": event_id,
                        "CUSTOMER_ID": cid,
                        "EVENT_TYPE": event_type,
                        "EVENT_TS": _iso(event_ts),
                        "CHANNEL": channel,
                        "TOPIC": topic,
                        "QUERY_OR_TITLE": query,
                        "RATING": None,
                        "SENTIMENT": round(rng.uniform(-0.3, 0.5) if is_help else rng.uniform(0.1, 0.8), 2),
                        "RESOLVED": None,
                        "DETAIL": "Session recorded in digital analytics.",
                    }
                )

    rows.sort(key=lambda r: (r["CUSTOMER_ID"], r["EVENT_TS"]))
    for idx, row in enumerate(rows, start=1):
        row["EVENT_ID"] = idx
    return rows
