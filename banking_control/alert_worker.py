from __future__ import annotations

import logging
import random
import threading
import time
from pathlib import Path

from banking_control.alert_generator import (
    ensure_alert_pool,
    expire_alerts_older_than,
    insert_transaction_alert,
    seconds_until_next_alert,
)
from banking_control.db import connect, prepare_connection, refresh_overview_cache

logger = logging.getLogger(__name__)


class TransactionAlertWorker:
    """Background thread: expire stale TM alerts and inject new ones at bank-like rates."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._rng = random.Random()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        if not self._db_path.is_file():
            logger.info("Alert worker skipped: database not found at %s", self._db_path)
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="tm-alert-generator",
            daemon=True,
        )
        self._bootstrap_pool()
        self._generate_once()
        self._thread.start()
        logger.info("Transaction monitoring alert generator started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

    def _loop(self) -> None:
        next_at = time.monotonic() + seconds_until_next_alert(self._rng)
        expire_at = time.monotonic() + 120.0
        while not self._stop.is_set():
            now = time.monotonic()
            if now >= next_at:
                self._generate_once()
                next_at = now + seconds_until_next_alert(self._rng)
            if now >= expire_at:
                self._expire_only()
                expire_at = now + 120.0
            wait = min(max(0.5, next_at - time.monotonic()), 30.0)
            self._stop.wait(timeout=wait)

    def _connect(self):
        conn = connect(self._db_path)
        prepare_connection(conn)
        return conn

    def _bootstrap_pool(self) -> None:
        try:
            conn = self._connect()
            try:
                added = ensure_alert_pool(conn, self._rng)
                if added:
                    conn.commit()
                    refresh_overview_cache(conn)
                    conn.commit()
                    logger.info("TM alert pool topped up with %s recent alerts", added)
            finally:
                conn.close()
        except Exception:
            logger.exception("TM alert pool bootstrap failed")

    def _generate_once(self) -> None:
        try:
            conn = self._connect()
            try:
                new_id = insert_transaction_alert(conn, self._rng)
                conn.commit()
                refresh_overview_cache(conn)
                conn.commit()
                if new_id:
                    logger.debug("TM alert created id=%s", new_id)
            finally:
                conn.close()
        except Exception:
            logger.exception("TM alert generation tick failed")

    def _expire_only(self) -> None:
        try:
            conn = self._connect()
            try:
                expired = expire_alerts_older_than(conn, days=2.0)
                added = ensure_alert_pool(conn, self._rng)
                if expired or added:
                    conn.commit()
                    refresh_overview_cache(conn)
                    conn.commit()
                if expired:
                    logger.debug("Expired %s TM alerts older than 2 days", expired)
                if added:
                    logger.debug("TM alert pool refilled with %s alerts after expiry", added)
            finally:
                conn.close()
        except Exception:
            logger.exception("TM alert expiry tick failed")
