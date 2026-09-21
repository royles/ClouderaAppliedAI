"""Train, persist, and score churn models."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from customer360.churn.features import (
    FEATURE_COLUMNS,
    derive_churn_label,
    feature_matrix,
    load_customer_frame,
)
from customer360.paths import default_db_path, project_root

MODEL_VERSION = "churn-lr-v3"
TARGET_PORTFOLIO_CHURN_RATE = 0.12
HIGH_TIER_FRACTION = 0.10
MEDIUM_TIER_FRACTION = 0.25
MODEL_DIR = project_root() / "data" / "models"
MODEL_PATH = MODEL_DIR / "churn_pipeline.joblib"
META_PATH = MODEL_DIR / "churn_model_meta.json"
CHURN_SCHEMA = project_root() / "data" / "churn_schema.sql"


def _calibrate_probabilities(raw: np.ndarray) -> np.ndarray:
    """Scale raw model scores to a realistic portfolio mean churn probability."""
    mean = float(np.mean(raw)) if len(raw) else TARGET_PORTFOLIO_CHURN_RATE
    if mean <= 1e-6:
        return np.full_like(raw, TARGET_PORTFOLIO_CHURN_RATE)
    scaled = raw * (TARGET_PORTFOLIO_CHURN_RATE / mean)
    return np.clip(scaled, 0.02, 0.85)


def _assign_risk_tiers(probabilities: np.ndarray) -> list[str]:
    """Rank-based tiers so synthetic book keeps ~10% HIGH / ~25% MEDIUM / ~65% LOW."""
    n = len(probabilities)
    if n == 0:
        return []
    order = np.argsort(probabilities, kind="stable")
    n_high = max(1, int(round(n * HIGH_TIER_FRACTION)))
    n_med = max(0, int(round(n * MEDIUM_TIER_FRACTION)))
    tiers = ["LOW"] * n
    for rank, idx in enumerate(order):
        if rank >= n - n_high:
            tiers[int(idx)] = "HIGH"
        elif rank >= n - n_high - n_med:
            tiers[int(idx)] = "MEDIUM"
    return tiers


def ensure_churn_table(conn: sqlite3.Connection) -> None:
    if CHURN_SCHEMA.is_file():
        conn.executescript(CHURN_SCHEMA.read_text(encoding="utf-8"))
        conn.commit()


def train_and_persist(db_path: Path | None = None) -> dict:
    db_path = db_path or default_db_path()
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        df = load_customer_frame(conn)
        if len(df) < 10:
            raise RuntimeError("Not enough customers to train churn model.")

        y = derive_churn_label(df)
        X = feature_matrix(df)

        if y.nunique() < 2:
            raise RuntimeError(
                "Churn labels are all one class; adjust label rules or seed data."
            )

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        pipeline = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=500,
                        class_weight={0: 1.0, 1: 2.5},
                        random_state=42,
                    ),
                ),
            ]
        )
        pipeline.fit(X_train, y_train)

        proba_test = pipeline.predict_proba(X_test)[:, 1]
        auc = float(roc_auc_score(y_test, proba_test))

        joblib.dump(pipeline, MODEL_PATH)
        meta = {
            "model_version": MODEL_VERSION,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "feature_columns": FEATURE_COLUMNS,
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "test_roc_auc": round(auc, 4),
            "churn_rate": round(float(y.mean()), 4),
        }
        META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        ensure_churn_table(conn)
        score_customers(conn, df, pipeline)
        try:
            from customer360.metrics_refresh import refresh_portfolio_analytics_cache

            refresh_portfolio_analytics_cache(conn)
        except Exception:
            pass
        conn.commit()

    return meta


def load_pipeline():
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Churn model not found at {MODEL_PATH}. Run the train churn job first."
        )
    return joblib.load(MODEL_PATH)


def score_customers(
    conn: sqlite3.Connection,
    df,
    pipeline,
) -> None:
    X = feature_matrix(df)
    raw = pipeline.predict_proba(X)[:, 1]
    probabilities = _calibrate_probabilities(raw)
    tiers = _assign_risk_tiers(probabilities)
    scored_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    conn.execute("DELETE FROM APP_CUSTOMER_CHURN_SCORES")
    rows = [
        (
            int(row.customer_id),
            round(float(prob), 6),
            tiers[i],
            MODEL_VERSION,
            scored_at,
        )
        for i, (row, prob) in enumerate(zip(df.itertuples(index=False), probabilities, strict=True))
    ]
    conn.executemany(
        """
        INSERT INTO APP_CUSTOMER_CHURN_SCORES (
            CUSTOMER_ID, CHURN_PROBABILITY, CHURN_RISK_TIER, MODEL_VERSION, SCORED_AT
        ) VALUES (?, ?, ?, ?, ?)
        """,
        rows,
    )
