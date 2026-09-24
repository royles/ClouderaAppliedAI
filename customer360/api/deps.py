"""FastAPI dependencies."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator

from customer360.db import connect


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
