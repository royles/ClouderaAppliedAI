"""FastAPI application exposing the sentiment classifier."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from . import model as model_module

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(
    title="Cloudera Applied AI - Sentiment Service",
    version=__version__,
    description="A minimal, self-contained sentiment analysis API used to "
    "validate the Cloud Agent development environment end to end.",
)

# The loaded pipeline is cached in module state after the first successful load.
_pipeline = None


def get_pipeline():
    """Lazily load and cache the trained pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = model_module.load()
    return _pipeline


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to classify.")


class PredictResponse(BaseModel):
    label: str
    confidence: float
    scores: dict[str, float]


@app.get("/health")
def health() -> dict:
    """Report service health and whether the model artifact is available."""
    try:
        get_pipeline()
        model_loaded = True
    except FileNotFoundError:
        model_loaded = False
    return {"status": "ok", "version": __version__, "model_loaded": model_loaded}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    """Classify a single piece of text as positive or negative sentiment."""
    try:
        pipeline = get_pipeline()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    result = model_module.predict(pipeline, request.text)
    return PredictResponse(
        label=result.label,
        confidence=result.confidence,
        scores=result.scores,
    )


@app.get("/")
def index() -> FileResponse:
    """Serve the single-page demo UI."""
    return FileResponse(STATIC_DIR / "index.html")


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
