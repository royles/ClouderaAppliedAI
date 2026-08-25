"""Training, persistence, and inference for the sentiment classifier."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .data import load_training_data

DEFAULT_MODEL_PATH = Path(
    os.environ.get("MODEL_PATH", Path(__file__).resolve().parent.parent / "models" / "sentiment.joblib")
)


@dataclass
class Prediction:
    label: str
    confidence: float
    scores: dict[str, float]


def build_pipeline() -> Pipeline:
    """Construct the TF-IDF + logistic regression pipeline."""
    return Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            # C=25 loosens L2 regularization so the classifier produces
            # confident probabilities on this intentionally small dataset.
            ("clf", LogisticRegression(max_iter=1000, C=25)),
        ]
    )


def train() -> Pipeline:
    """Train the model on the bundled dataset and return the fitted pipeline."""
    texts, labels = load_training_data()
    pipeline = build_pipeline()
    pipeline.fit(texts, labels)
    return pipeline


def save(pipeline: Pipeline, path: Path | str = DEFAULT_MODEL_PATH) -> Path:
    """Persist a fitted pipeline to disk, creating parent directories."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path)
    return path


def load(path: Path | str = DEFAULT_MODEL_PATH) -> Pipeline:
    """Load a persisted pipeline from disk."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Model artifact not found at {path}. Run `python -m scripts.train` first."
        )
    return joblib.load(path)


def predict(pipeline: Pipeline, text: str) -> Prediction:
    """Return a structured prediction for a single input string."""
    classes = list(pipeline.classes_)
    probabilities = pipeline.predict_proba([text])[0]
    scores = {label: float(prob) for label, prob in zip(classes, probabilities)}
    best_label = max(scores, key=scores.get)
    return Prediction(label=best_label, confidence=scores[best_label], scores=scores)
