"""Unit tests for the model training and inference layer."""

from __future__ import annotations

from pathlib import Path

from app import model as model_module


def test_train_and_predict_positive():
    pipeline = model_module.train()
    result = model_module.predict(pipeline, "I love this, it is wonderful and great")
    assert result.label == "positive"
    assert 0.0 <= result.confidence <= 1.0
    assert set(result.scores) == {"positive", "negative"}


def test_train_and_predict_negative():
    pipeline = model_module.train()
    result = model_module.predict(pipeline, "This is terrible, awful and broken")
    assert result.label == "negative"


def test_save_and_load_roundtrip(tmp_path: Path):
    pipeline = model_module.train()
    artifact = model_module.save(pipeline, tmp_path / "sentiment.joblib")
    assert artifact.exists()

    loaded = model_module.load(artifact)
    result = model_module.predict(loaded, "absolutely fantastic experience")
    assert result.label == "positive"


def test_scores_sum_to_one():
    pipeline = model_module.train()
    result = model_module.predict(pipeline, "a pleasant and delightful day")
    assert abs(sum(result.scores.values()) - 1.0) < 1e-6
