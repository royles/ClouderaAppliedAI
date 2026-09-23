"""Overview domain card counts (warehouse + optional cache)."""

from __future__ import annotations

import sqlite3

from customer360.api.policy_counts import policy_totals_for_segment
from customer360.api.schemas import DomainCount
from customer360.api.segments import OVERVIEW_DOMAINS
from customer360.db import sqlite_table_exists


def fetch_overview_domains(conn: sqlite3.Connection) -> list[DomainCount]:
    cache_ready = sqlite_table_exists(conn, "APP_OVERVIEW_COUNTS")
    domains: list[DomainCount] = []
    for label, filter_key, description, count_sql in OVERVIEW_DOMAINS:
        if cache_ready:
            row = conn.execute(
                "SELECT ROW_COUNT FROM APP_OVERVIEW_COUNTS WHERE FILTER_KEY = ?",
                (filter_key,),
            ).fetchone()
            row_count = int(row[0]) if row else int(conn.execute(count_sql).fetchone()[0])
        else:
            row_count = int(conn.execute(count_sql).fetchone()[0])
        total_policies, active_policies = policy_totals_for_segment(conn, filter_key)
        domains.append(
            DomainCount(
                domain=label,
                row_count=row_count,
                filter_key=filter_key,
                description=description,
                policy_total=total_policies,
                policy_active=active_policies,
            )
        )
    return domains
