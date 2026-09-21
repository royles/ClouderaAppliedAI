#!/usr/bin/env python3
"""Create and seed the Customer 360 SQLite warehouse."""

from __future__ import annotations

import argparse
import calendar
import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from customer360.interactions.seed import build_interaction_events
from customer360.admin_store import ensure_admin_schema
from customer360.kpi_benchmarks import ensure_kpi_benchmark_catalog
from customer360.paths import default_db_path, project_root, schema_path

INTERACTIONS_SCHEMA = project_root() / "data" / "interactions_schema.sql"

RNG = random.Random(36085)

CUSTOMER_TYPE_MAP = {
    1: "Teudat Zehut",
    2: "Passport",
    3: "Military ID",
    5: "Corporation",
}

MARITAL_MAP = {
    "נ": "Single",
    "ג": "Married",
    "ר": "Divorced",
    "א": "Widowed",
}

COMM_MAP = {
    1: "Email",
    2: "Mail",
    6: "SMS",
}

FIRST_NAMES = [
    "David", "Sarah", "Yosef", "Michal", "Avi", "Noa", "Eitan", "Shira",
    "Ron", "Tamar", "Amir", "Hila", "Omer", "Yael", "Itay", "Rachel",
    "Daniel", "Leah", "Tom", "Maya",
]

LAST_NAMES = [
    "Cohen", "Levi", "Mizrahi", "Peretz", "Biton", "Azoulay", "Dahan",
    "Abraham", "Friedman", "Goldstein", "Shapiro", "Katz", "Rosenberg",
    "Ben-David", "Avraham", "Mor", "Barak", "Golan", "Shalev", "Nagar",
]

CITIES = [
    ("Tel Aviv", "Rothschild Blvd", 6370001),
    ("Jerusalem", "Jaffa Road", 9422701),
    ("Haifa", "Herzl Street", 3300000),
    ("Beer Sheva", "Rager Blvd", 8448101),
    ("Netanya", "Herzl Street", 4226001),
    ("Ashdod", "Menachem Begin Blvd", 7745701),
    ("Rishon LeZion", "Herzl Street", 7528501),
    ("Petah Tikva", "Jabotinsky Street", 4910000),
]

POLICY_TYPES = [
    (101, "Life Insurance"),
    (102, "Critical Illness"),
    (201, "Health Supplementary"),
    (301, "Elementary Property"),
    (401, "Pension Fund"),
    (402, "Provident Fund"),
    (403, "Study Fund"),
]

POLICY_STATUS_ACTIVE = [
    (10, "Active"),
    (20, "Premium Paying"),
    (45, "Paid Up"),
]
POLICY_STATUS_INACTIVE = [
    (55, "Lapsed"),
    (60, "Surrendered"),
]
POLICY_STATUS = POLICY_STATUS_ACTIVE + POLICY_STATUS_INACTIVE

# Portfolio mix: ~72% engaged, ~20% stable/watch, ~8% at-risk (industry-like spread).
SEGMENT_WEIGHTS = ("engaged", 0.72), ("stable", 0.20), ("at_risk", 0.08)


def _assign_engagement_segment() -> str:
    roll = RNG.random()
    cumulative = 0.0
    for name, weight in SEGMENT_WEIGHTS:
        cumulative += weight
        if roll <= cumulative:
            return name
    return "engaged"


def _customer_rows_for_db(customers: list[dict]) -> list[dict]:
    return [{k: v for k, v in row.items() if not str(k).startswith("_")} for row in customers]

EMPLOYERS = [
    (1001, "Intel Israel"),
    (1002, "Tehila Tech Ltd"),
    (1003, "Maccabi Healthcare"),
    (1004, "Israel Electric Corp"),
    (1005, "Bank Hapoalim"),
]

FUNDS = [
    (7, 5101, "General Pension Track — Balanced"),
    (7, 5102, "General Pension Track — Equity"),
    (1, 2101, "Life Savings — Conservative"),
    (1, 2102, "Life Savings — Growth"),
    (8, 8101, "Gemel — Multi-Sector"),
    (8, 8102, "Gemel — Index 500"),
]

CORP_NAMES = {
    1: "Phoenix Life Insurance",
    7: "Clal Pension",
    8: "Meitav Dash Gemel",
}


def iso(d: date | datetime) -> str:
    if isinstance(d, datetime):
        return d.strftime("%Y-%m-%d %H:%M:%S")
    return d.isoformat()


def last_day_of_month(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def month_id(d: date) -> int:
    return d.year * 100 + d.month


def generate_israeli_id(rng: random.Random) -> int:
    """Generate a plausible 9-digit ID (not checksum-validated)."""
    base = rng.randint(100_000_000, 399_999_999)
    return base


DEFAULT_SEED_CUSTOMERS = 40
MAX_SEED_CUSTOMERS = 5000


def build_customers(n: int = DEFAULT_SEED_CUSTOMERS) -> list[dict]:
    rows: list[dict] = []
    used_ids: set[int] = set()
    now = datetime(2025, 9, 15, 10, 30, 0)

    for i in range(n):
        cid = generate_israeli_id(RNG)
        while cid in used_ids:
            cid = generate_israeli_id(RNG)
        used_ids.add(cid)

        corp_slots = max(2, n // 200)
        ctype = 1 if i < n - corp_slots else RNG.choice([2, 5])
        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        last = LAST_NAMES[(i // len(FIRST_NAMES)) % len(LAST_NAMES)]
        city, street, zipcode = CITIES[i % len(CITIES)]
        marital_code = RNG.choice(list(MARITAL_MAP.keys()))
        comm = RNG.choice([1, 2, 6])
        smoker = RNG.choice(["0", "1"])
        kosher = "KOSHER_MOBILE" if RNG.random() < 0.15 else "NO"
        birth = date(RNG.randint(1955, 2000), RNG.randint(1, 12), RNG.randint(1, 28))
        gender = RNG.choice([1, 2])
        prefix = RNG.choice(["050", "052", "053", "054", "058"])
        mobile = f"{prefix}-{RNG.randint(1000000, 9999999)}"
        email = f"{first.lower()}.{last.lower()}{i}@example.co.il"
        segment = _assign_engagement_segment()
        if segment == "engaged":
            registered = 1 if RNG.random() < 0.88 else 0
            last_login = (
                now - timedelta(days=RNG.randint(1, 45)) if registered else None
            )
        elif segment == "stable":
            registered = 1 if RNG.random() < 0.55 else 0
            if registered:
                last_login = now - timedelta(days=RNG.randint(20, 100))
            else:
                last_login = None
        else:
            registered = 1 if RNG.random() < 0.7 else 0
            last_login = (
                now - timedelta(days=RNG.randint(95, 320)) if registered else None
            )

        key = f"CK-{cid}"
        rows.append(
            {
                "_segment": segment,
                "CUSTOMER_KEY": key,
                "CUSTOMER_ID": cid,
                "CUSTOMER_ID_CHAR": str(cid),
                "CUSTOMER_TYPE": ctype,
                "CUSTOMER_TYPE_DSC": CUSTOMER_TYPE_MAP[ctype],
                "FIRST_NAME": first,
                "LAST_NAME": last,
                "CUSTOMER_NAME": f"{first} {last}",
                "GENDER_CODE": gender,
                "BIRTH_DATE": iso(birth),
                "MARITAL_STATUS_CODE": marital_code,
                "MARITAL_STATUS_DSC": MARITAL_MAP[marital_code],
                "OCCUPATION_CODE": RNG.randint(100, 999),
                "SMOKER_STATUS_CODE": smoker,
                "EMAIL": email,
                "MOBILE_NO": mobile,
                "IS_MOBILE_KOSHER": kosher,
                "CITY_NAME": city,
                "STREET_NAME": street,
                "HOUSE_NO": RNG.randint(1, 120),
                "ZIPCODE": zipcode,
                "COMMUNICATION_CODE": comm,
                "COMMUNICATION_DSC": COMM_MAP[comm],
                "LAST_LOGIN": iso(last_login) if last_login else None,
                "USER_SITE_REGISTER_STATUS": registered,
                "DWH_INSERT_DATE": iso(now - timedelta(days=RNG.randint(30, 800))),
                "DWH_CLOSE_DATE": "2999-12-31",
                "CURRENT_IND": 1,
            }
        )

    # SCD Type 2 history row for first customer
    hist = dict(rows[0])
    hist["CUSTOMER_KEY"] = f"{rows[0]['CUSTOMER_KEY']}-HIST"
    hist["EMAIL"] = "old.email@example.co.il"
    hist["DWH_CLOSE_DATE"] = "2024-06-30"
    hist["CURRENT_IND"] = 0
    rows.append(hist)

    return rows


def _pick_policy_status(segment: str, *, allow_inactive: bool) -> tuple[int, str, int]:
    if segment == "engaged":
        status_code, status_desc = RNG.choice(POLICY_STATUS_ACTIVE)
        return status_code, status_desc, 1
    if segment == "at_risk" and (allow_inactive or RNG.random() < 0.55):
        status_code, status_desc = RNG.choice(POLICY_STATUS_INACTIVE)
        return status_code, status_desc, 0
    if segment == "stable" and allow_inactive and RNG.random() < 0.35:
        status_code, status_desc = RNG.choice(POLICY_STATUS_INACTIVE)
        return status_code, status_desc, 0
    status_code, status_desc = RNG.choices(
        POLICY_STATUS_ACTIVE,
        weights=[45, 40, 15],
        k=1,
    )[0]
    return status_code, status_desc, 1


def build_policies(customers: list[dict]) -> list[dict]:
    rows: list[dict] = []
    policy_seq = 100000

    active_customers = [c for c in customers if c["CURRENT_IND"] == 1]
    for cust in active_customers:
        segment = cust.get("_segment", "engaged")
        if segment == "engaged":
            n_policies = RNG.randint(2, 4)
        elif segment == "stable":
            n_policies = RNG.randint(1, 3)
        else:
            n_policies = RNG.randint(1, 2)

        has_active = False
        for policy_idx in range(n_policies):
            policy_seq += 1
            ptype_code, ptype_desc = RNG.choice(POLICY_TYPES)
            mng = {101: 1, 102: 1, 201: 1, 301: 9, 401: 7, 402: 8, 403: 8}[ptype_code]
            allow_inactive = policy_idx > 0 or segment != "engaged"
            status_code, status_desc, is_active = _pick_policy_status(
                segment, allow_inactive=allow_inactive
            )
            if is_active:
                has_active = True
            elif policy_idx == n_policies - 1 and not has_active and segment != "at_risk":
                status_code, status_desc = RNG.choice(POLICY_STATUS_ACTIVE)
                is_active = 1
                has_active = True
            start = date(RNG.randint(2005, 2022), RNG.randint(1, 12), RNG.randint(1, 28))
            end = date(2099, 12, 31) if is_active else date(RNG.randint(2020, 2025), RNG.randint(1, 12), 28)
            collective = 1 if ptype_code in (401, 402) and RNG.random() < 0.4 else 0
            employer_num, employer_desc = (None, None)
            if collective:
                employer_num, employer_desc = RNG.choice(EMPLOYERS)
            premium = round(RNG.uniform(150, 4500), 2) if ptype_code != 301 else round(RNG.uniform(80, 600), 2)
            liquidity = None
            if mng in (7, 8):
                liquidity = iso(start + timedelta(days=RNG.randint(365 * 3, 365 * 10)))

            rows.append(
                {
                    "POLICY_KEY": f"{mng}-{policy_seq}",
                    "CUSTOMER_ID": str(cust["CUSTOMER_ID"]),
                    "CUSTOMER_KEY": cust["CUSTOMER_KEY"],
                    "MNG_COMPANY_CODE": mng,
                    "COMPANY_CODE": 1 if mng == 9 else mng,
                    "POLICY_NUM": policy_seq,
                    "POLICY_TYPE_CODE": ptype_code,
                    "POLICY_TYPE_DESC": ptype_desc,
                    "POLICY_START_DATE": iso(start),
                    "POLICY_END_DATE": iso(end),
                    "IS_ACTIVE": is_active,
                    "POLICY_STATUS_CODE": status_code,
                    "POLICY_STATUS_DESC": status_desc,
                    "IS_COLECTIVE": collective,
                    "EMPLOYER_NUM": employer_num,
                    "EMPLOYER_DESC": employer_desc,
                    "BRUTO_MONTHLY_PREMIUM": premium,
                    "AGENT_NUMBER": RNG.randint(10000, 99999),
                    "DISTRICT_NUM": RNG.randint(1, 6),
                    "LIQUIDITY_DATE": liquidity,
                }
            )
    return rows


def build_foreclosures(
    customers: list[dict],
    policies: list[dict],
    *,
    target_fraction: float = 0.018,
    min_targets: int = 6,
) -> tuple[list[dict], list[dict]]:
    fc_rows: list[dict] = []
    asset_rows: list[dict] = []
    active = [c for c in customers if c["CURRENT_IND"] == 1]
    at_risk = [c for c in active if c.get("_segment") == "at_risk"]
    stable = [c for c in active if c.get("_segment") == "stable"]
    engaged = [c for c in active if c.get("_segment") == "engaged"]
    target_count = max(min_targets, int(len(active) * target_fraction))
    target_count = min(target_count, len(active))

    targets: list[dict] = []
    if at_risk:
        targets.extend(RNG.sample(at_risk, min(len(at_risk), max(1, int(target_count * 0.55)))))
    remaining = target_count - len(targets)
    if remaining > 0 and stable:
        targets.extend(RNG.sample(stable, min(len(stable), max(0, int(target_count * 0.35)))))
    remaining = target_count - len(targets)
    if remaining > 0 and engaged:
        pool = [c for c in engaged if c not in targets]
        if pool:
            targets.extend(RNG.sample(pool, min(len(pool), remaining)))
    if len(targets) < min(target_count, len(active)):
        pool = [c for c in active if c not in targets]
        if pool:
            targets.extend(RNG.sample(pool, min(len(pool), target_count - len(targets))))
    spuror = 5000

    for cust in targets:
        spuror += 1
        fc_num = RNG.randint(100000, 999999)
        amount = round(RNG.uniform(5000, 250000), 2)
        fc_date = date(RNG.randint(2019, 2024), RNG.randint(1, 12), RNG.randint(1, 28))
        reg_date = fc_date + timedelta(days=RNG.randint(5, 45))
        cust_policies = [p for p in policies if p["CUSTOMER_KEY"] == cust["CUSTOMER_KEY"] and p["IS_ACTIVE"]]

        fc_rows.append(
            {
                "COMPANY_NUMBER": 1,
                "CUSTOMER_ID": str(cust["CUSTOMER_ID"]),
                "FORECLOSURES_NUMBER": fc_num,
                "PORTFOLIO_NUMBER": RNG.randint(1000, 9999),
                "FORECLOSURES_AMOUNT": amount,
                "FORECLOSURES_DATE": iso(fc_date),
                "REGIST_DATE": iso(reg_date),
                "SPUROR_NUMBER": spuror,
            }
        )

        if cust_policies:
            pol = RNG.choice(cust_policies)
            asset_rows.append(
                {
                    "SPUROR_NUMBER": spuror,
                    "COMPANY_ID": pol["COMPANY_CODE"],
                    "CUSTOMER_ID": str(cust["CUSTOMER_ID"]),
                    "IND_EXIST": "כן",
                    "ASSETS_SOURCE": "AS400-IKULIMF",
                    "POLICY_OR_CLAIM": "פוליסה",
                    "POLICY_NUM": pol["POLICY_NUM"],
                    "CLAIM_NUM": 0,
                    "IND_RELAVANT_ASSET": 1,
                    "FIRST_DATE_LOCATE_ASSET": iso(fc_date + timedelta(days=RNG.randint(10, 90))),
                }
            )
        if RNG.random() < 0.35:
            claim_num = RNG.randint(200000, 299999)
            asset_rows.append(
                {
                    "SPUROR_NUMBER": spuror,
                    "COMPANY_ID": 1,
                    "CUSTOMER_ID": str(cust["CUSTOMER_ID"]),
                    "IND_EXIST": RNG.choice(["כן", "לא"]),
                    "ASSETS_SOURCE": "Claims-NOGA",
                    "POLICY_OR_CLAIM": "תביעה",
                    "POLICY_NUM": 0,
                    "CLAIM_NUM": claim_num,
                    "IND_RELAVANT_ASSET": 1,
                    "FIRST_DATE_LOCATE_ASSET": iso(fc_date + timedelta(days=RNG.randint(30, 120))),
                }
            )

    return fc_rows, asset_rows


def build_policy_investment_tracks(policies: list[dict], months: list[date]) -> list[dict]:
    rows: list[dict] = []
    invest_policies = [p for p in policies if p["MNG_COMPANY_CODE"] in (1, 7, 8) and p["IS_ACTIVE"]]

    for pol in invest_policies:
        fund_choices = [f for f in FUNDS if f[0] == pol["MNG_COMPANY_CODE"]]
        if not fund_choices:
            fund_choices = FUNDS[:2]
        tracks = RNG.sample(fund_choices, k=min(len(fund_choices), RNG.randint(1, 2)))
        policy_key = int("".join(c for c in pol["POLICY_KEY"] if c.isdigit())[-8:])

        rewards = RNG.uniform(80000, 450000)
        comp = RNG.uniform(20000, 180000)

        for snap in months:
            growth = 1 + RNG.uniform(-0.02, 0.035)
            rewards *= growth
            comp *= 1 + RNG.uniform(-0.015, 0.025)
            total = rewards + comp
            ytd_r = round(RNG.uniform(-5000, 25000), 2)
            ytd_t = round(ytd_r + RNG.uniform(-3000, 15000), 2)

            for track_id, (_, fund_id, _) in enumerate(tracks, start=1):
                split = 1 / len(tracks)
                rows.append(
                    {
                        "POLICY_KEY": policy_key,
                        "SNAPSHOT_DATE": iso(last_day_of_month(snap.year, snap.month)),
                        "MONTH_ID": month_id(snap),
                        "MNG_COMPANY_CODE": pol["MNG_COMPANY_CODE"],
                        "COMPANY_CODE": pol["COMPANY_CODE"],
                        "CUSTOMER_ID": int(pol["CUSTOMER_ID"]),
                        "POLICY_NUM": pol["POLICY_NUM"],
                        "INVESTMENT_TRACK_ID": track_id,
                        "FUND_ID": fund_id,
                        "ACCUMULATION_REWARDS": round(rewards * split, 2),
                        "ACCUMULATION_COMPENSATION": round(comp * split, 2),
                        "ACCUMULATION_TOTAL": round(total * split, 2),
                        "YEARLY_PROFIT_LOSS_REWARDS": round(ytd_r * split, 2),
                        "YEARLY_PROFIT_LOSS_TOTAL": round(ytd_t * split, 2),
                    }
                )
    return rows


def build_market_tracks(months: list[date]) -> list[dict]:
    rows: list[dict] = []
    for snap in months:
        snap_d = last_day_of_month(snap.year, snap.month)
        mid = month_id(snap_d)
        for mng, fund_id, fund_name in FUNDS:
            monthly_yield = round(RNG.uniform(-2.5, 3.5), 4)
            rows.append(
                {
                    "MONTH_ID": mid,
                    "SNAPSHOT_DATE": iso(snap_d),
                    "MNG_COMPANY_CODE": mng,
                    "PRODUCT_TYPE_CODE": {1: 10, 7: 20, 8: 30}[mng],
                    "FUND_ID": fund_id,
                    "FUND_NAME": fund_name,
                    "MANAGING_CORPORATION_LEGAL_ID": 512345678 + mng,
                    "MANAGING_CORPORATION": CORP_NAMES[mng],
                    "MONTHLY_YIELD": monthly_yield,
                    "YEAR_TO_DATE_YIELD": round(RNG.uniform(-5, 12), 4),
                    "YIELD_TRAILING_3_YRS": round(RNG.uniform(2, 10), 4),
                    "YIELD_TRAILING_5_YRS": round(RNG.uniform(3, 9), 4),
                    "ALPHA": round(RNG.uniform(-1, 2), 4),
                    "SHARPE_RATIO": round(RNG.uniform(0.2, 1.5), 4),
                    "LIQUID_ASSETS_PERCENT": round(RNG.uniform(5, 35), 2),
                    "STOCK_MARKET_EXPOSURE": round(RNG.uniform(15, 75), 2),
                    "TOTAL_ASSETS": round(RNG.uniform(500_000_000, 12_000_000_000), 2),
                }
            )
    return rows


def build_policy_status_snapshots(policies: list[dict], months: list[date]) -> list[dict]:
    rows: list[dict] = []
    life_health = [p for p in policies if p["POLICY_TYPE_CODE"] in (101, 102, 201)]

    for pol in life_health:
        base_sum = RNG.uniform(200_000, 2_500_000)
        for snap in months[-3:]:
            snap_d = last_day_of_month(snap.year, snap.month)
            premium = pol["BRUTO_MONTHLY_PREMIUM"] or 0
            surrender = round(base_sum * RNG.uniform(0.05, 0.35), 2)
            savings = round(base_sum * RNG.uniform(0.1, 0.5), 2)
            rows.append(
                {
                    "COMPANY_CODE": pol["COMPANY_CODE"],
                    "SNAPSHOT_DATE": iso(snap_d),
                    "CUSTOMER_ID": int(pol["CUSTOMER_ID"]),
                    "POLICY_NUM": pol["POLICY_NUM"],
                    "POLICY_STATUS_CODE": pol["POLICY_STATUS_CODE"],
                    "POLICY_STATUS_DESC": pol["POLICY_STATUS_DESC"],
                    "SUM_INSURED_AMOUNT": round(base_sum, 2),
                    "MONTHLY_PREMIUM": round(premium, 2),
                    "DEATH_BENEFIT_AMOUNT": round(base_sum * RNG.uniform(0.8, 1.0), 2),
                    "SURRENDER_VALUE": surrender,
                    "PAID_UP_VALUE": round(surrender * 0.9, 2),
                    "SAVINGS_BALANCE": savings,
                    "PREMIUM_MANAGEMENT_FEE": round(premium * 0.02, 2),
                    "SAVINGS_MANAGEMENT_FEE": round(savings * 0.004, 2),
                    "EMPLOYER_BENEFIT_AMOUNT": round(savings * 0.25, 2),
                }
            )
    return rows


def insert_rows(
    conn: sqlite3.Connection,
    table: str,
    rows: list[dict],
    *,
    chunk_size: int = 5000,
) -> None:
    if not rows:
        return
    cols = list(rows[0].keys())
    placeholders = ", ".join("?" for _ in cols)
    col_sql = ", ".join(cols)
    sql = f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})"
    for start in range(0, len(rows), chunk_size):
        batch = rows[start : start + chunk_size]
        conn.executemany(sql, [tuple(r[c] for c in cols) for r in batch])


def init_database(
    db_path: Path,
    rebuild: bool = True,
    *,
    customer_count: int = DEFAULT_SEED_CUSTOMERS,
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if rebuild and db_path.exists():
        db_path.unlink()

    n = max(1, min(int(customer_count), MAX_SEED_CUSTOMERS))
    if n != customer_count:
        print(f"Note: customer_count clamped to {n} (max {MAX_SEED_CUSTOMERS})", flush=True)

    months = [date(2025, m, 1) for m in range(1, 10)]

    print(f"Generating {n} representative customers…", flush=True)
    customers = build_customers(n)
    print("Building policies…", flush=True)
    policies = build_policies(customers)
    print("Building foreclosures, investments, coverage snapshots…", flush=True)
    foreclosures, fc_assets = build_foreclosures(customers, policies)
    pit = build_policy_investment_tracks(policies, months)
    market = build_market_tracks(months)
    policy_status = build_policy_status_snapshots(policies, months)
    print("Building interaction events…", flush=True)
    interactions = build_interaction_events(customers, policies, foreclosures, rng=RNG)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.executescript(schema_path().read_text(encoding="utf-8"))
        if INTERACTIONS_SCHEMA.is_file():
            conn.executescript(INTERACTIONS_SCHEMA.read_text(encoding="utf-8"))
        churn_schema = project_root() / "data" / "churn_schema.sql"
        if churn_schema.is_file():
            conn.executescript(churn_schema.read_text(encoding="utf-8"))
        insights_schema = project_root() / "data" / "insights_schema.sql"
        if insights_schema.is_file():
            conn.executescript(insights_schema.read_text(encoding="utf-8"))
        metrics_schema = project_root() / "data" / "metrics_schema.sql"
        if metrics_schema.is_file():
            conn.executescript(metrics_schema.read_text(encoding="utf-8"))

        print("Writing warehouse tables…", flush=True)
        insert_rows(conn, "DWH_DIM_CUSTOMERS_UNIQUE", _customer_rows_for_db(customers))
        insert_rows(conn, "DWH_DIM_ALL_POLICY", policies)
        insert_rows(conn, "DWH_FCT_FORECLOSURES", foreclosures)
        insert_rows(conn, "DWH_FCT_FORECLOSURES_ASSETS", fc_assets)
        insert_rows(conn, "DWH_FCT_POLICY_INVESTMENT_TRACK", pit)
        insert_rows(conn, "DWH_FCT_INVESTMENT_TRACK", market)
        insert_rows(conn, "DWH_FCT_POLICY_STATUS", policy_status)
        insert_rows(conn, "APP_CUSTOMER_INTERACTION_EVENTS", interactions)
        conn.commit()

        from customer360.metrics_refresh import (
            refresh_customer_metrics,
            refresh_overview_counts,
        )

        print("Precomputing customer list metrics and overview counts…", flush=True)
        refresh_customer_metrics(conn)
        refresh_overview_counts(conn)
        from customer360.api.warehouse_admin import refresh_warehouse_manifest

        refresh_warehouse_manifest(conn, source_job="seed")

        counts = conn.execute(
            """
            SELECT 'DWH_DIM_CUSTOMERS_UNIQUE' AS tbl, COUNT(*) FROM DWH_DIM_CUSTOMERS_UNIQUE
            UNION ALL SELECT 'DWH_DIM_ALL_POLICY', COUNT(*) FROM DWH_DIM_ALL_POLICY
            UNION ALL SELECT 'DWH_FCT_FORECLOSURES', COUNT(*) FROM DWH_FCT_FORECLOSURES
            UNION ALL SELECT 'DWH_FCT_FORECLOSURES_ASSETS', COUNT(*) FROM DWH_FCT_FORECLOSURES_ASSETS
            UNION ALL SELECT 'DWH_FCT_POLICY_INVESTMENT_TRACK', COUNT(*) FROM DWH_FCT_POLICY_INVESTMENT_TRACK
            UNION ALL SELECT 'DWH_FCT_INVESTMENT_TRACK', COUNT(*) FROM DWH_FCT_INVESTMENT_TRACK
            UNION ALL SELECT 'DWH_FCT_POLICY_STATUS', COUNT(*) FROM DWH_FCT_POLICY_STATUS
            UNION ALL SELECT 'APP_CUSTOMER_INTERACTION_EVENTS', COUNT(*) FROM APP_CUSTOMER_INTERACTION_EVENTS
            """
        ).fetchall()

    admin_conn = ensure_admin_schema()
    ensure_kpi_benchmark_catalog(admin_conn)
    admin_conn.close()

    print(f"Database written to {db_path}")
    for name, count in counts:
        print(f"  {name}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="SQLite database path (default: CUSTOMER360_DB_PATH or data/customer360.db)",
    )
    parser.add_argument(
        "--no-rebuild",
        action="store_true",
        help="Append to existing DB without deleting (schema still applied)",
    )
    parser.add_argument(
        "--customers",
        type=int,
        default=DEFAULT_SEED_CUSTOMERS,
        metavar="N",
        help=f"Number of current customers to generate (max {MAX_SEED_CUSTOMERS}, default {DEFAULT_SEED_CUSTOMERS})",
    )
    args = parser.parse_args()
    db_path = args.db or default_db_path()
    init_database(
        db_path,
        rebuild=not args.no_rebuild,
        customer_count=args.customers,
    )


if __name__ == "__main__":
    main()
