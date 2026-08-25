# ClouderaAppliedAI

A minimal, self-contained **Applied AI** reference service: a sentiment
analysis model (TF-IDF + Logistic Regression, scikit-learn) served through a
**FastAPI** HTTP API with a small single-page web UI.

It is intentionally dependency-light and works fully offline — the model trains
on a small bundled dataset — so the whole pipeline (train → serve → predict) can
be demonstrated end to end in a fresh Cloud Agent environment with no external
services, accounts, or API keys.

## Project layout

```
app/            FastAPI app + model training/inference logic
  data.py       Bundled labeled dataset
  model.py      Train / save / load / predict
  main.py       API endpoints (/health, /predict, /) and static UI mount
scripts/train.py  Trains and persists the model artifact (models/sentiment.joblib)
static/index.html Single-page demo UI
tests/          pytest unit + API tests
.cursor/        Cloud Agent environment scripts (install.sh, start.sh)
```

## Quick start

```bash
# 1. Install dependencies and train the model (idempotent)
bash .cursor/install.sh

# 2. Run the API server
bash .cursor/start.sh
# -> http://localhost:8000  (web UI)
```

In the Cloud Agent environment these are wired up as the `install` command
(`bash .cursor/install.sh`) and the `start` command (`bash .cursor/start.sh`),
so the service is already running when an agent starts.

### Manual (without the helper scripts)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.train
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API

| Method | Path        | Description                                   |
| ------ | ----------- | --------------------------------------------- |
| GET    | `/health`   | Service status and whether the model is loaded |
| POST   | `/predict`  | `{ "text": "..." }` → `{ label, confidence, scores }` |
| GET    | `/`         | Web UI                                        |

Example:

```bash
curl -s -X POST http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"text":"I absolutely love this product"}'
# {"label":"positive","confidence":0.87,"scores":{"negative":0.13,"positive":0.87}}
```

## Tests

```bash
source .venv/bin/activate
python -m pytest
```

## Configuration

- `MODEL_PATH` — override where the trained model artifact is read/written
  (default `models/sentiment.joblib`).
