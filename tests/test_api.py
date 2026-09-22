"""End-to-end API tests exercised through the FastAPI test client."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import model as model_module
from app.main import app


@pytest.fixture(autouse=True)
def ensure_model(tmp_path, monkeypatch):
    """Train a fresh model into a temp path and point the app at it."""
    artifact = tmp_path / "sentiment.joblib"
    pipeline = model_module.train()
    model_module.save(pipeline, artifact)
    monkeypatch.setattr(model_module, "DEFAULT_MODEL_PATH", artifact)
    # Reset the cached pipeline so the app reloads from the temp artifact.
    import app.main as main_module

    main_module._pipeline = None
    yield
    main_module._pipeline = None


def test_health_ok():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_predict_positive():
    client = TestClient(app)
    res = client.post("/predict", json={"text": "I love this amazing product"})
    assert res.status_code == 200
    body = res.json()
    assert body["label"] == "positive"
    assert 0.0 <= body["confidence"] <= 1.0


def test_predict_negative():
    client = TestClient(app)
    res = client.post("/predict", json={"text": "this is the worst and most awful thing"})
    assert res.status_code == 200
    assert res.json()["label"] == "negative"


def test_predict_validation_error():
    client = TestClient(app)
    res = client.post("/predict", json={"text": ""})
    assert res.status_code == 422


def test_index_served():
    client = TestClient(app)
    res = client.get("/")
    assert res.status_code == 200
    assert "Cloudera Applied AI" in res.text
