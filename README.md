# ClouderaAppliedAI

## Development workflow

**Use `main` only.** New fixes and features are committed and pushed directly to
`main` (no long-lived feature branches). Pull before you work; push when done.

```bash
git checkout main
git pull origin main
# … edit, test …
git add -A && git commit -m "Describe the change"
git push origin main
```

### Get the latest code on another machine

```bash
git fetch origin
git checkout main
git pull origin main
```

If `git pull` says **Already up to date** but the app looks old, run
`git branch --show-current` — it must be **`main`**, not an old `cursor/*` branch.
Then restart the API and hard-refresh the browser (`frontend/dist` is committed with
the app).

## Insurance Customer 360

Unified customer dashboard for Cloudera AI (CAI), backed by a DDS-aligned SQLite warehouse.

### Deploy on Cloudera AI

This repo is packaged as a **CAI application (AMP)** via `.project-metadata.yaml` and
`amp-catalog.yaml`. Step-by-step instructions: [docs/CAI_APPLICATION.md](docs/CAI_APPLICATION.md).

1. Create a project from this Git repository and **configure as prototype**, or launch from your
   AMP catalog entry (**Insurance Customer 360**).
2. On first import, `.project-metadata.yaml` runs these stages in order:

   | Stage | Folder / script | Purpose |
   | --- | --- | --- |
   | 1 | `1_session-install-dependencies/` | Python deps + editable `customer360` install |
   | 2 | `scripts/build_frontend.py` | `npm run build` → `frontend/dist` |
   | 3 | `2_job-init-database/` | Seed `data/customer360.db` |
   | 4 | `3_job-train-churn-model/` | Churn model → `APP_CUSTOMER_CHURN_SCORES` |
   | 5 | `4_application/start-app.py` | FastAPI + React dashboard |
3. Application scripts bind to `127.0.0.1` and use `CDSW_APP_PORT` (Workbench/CML) or `APP_PORT` (AI Inference, default 8080). Do not hard-code ports.

Optional environment variable:

| Variable | Default | Purpose |
| --- | --- | --- |
| `CUSTOMER360_DB_PATH` | `data/customer360.db` | SQLite file (relative to `CDSW_PROJECT`) |
| `AWS_*`, `CUSTOMER360_BEDROCK_*` | — | Amazon Bedrock (insights + outreach drafts); see `.env.example` |

### Project layout (CAI-compatible)

```
.
├── .project-metadata.yaml          # CAI AMP import + application tasks
├── amp-catalog.yaml                # Optional AMP catalog registration
├── docs/CAI_APPLICATION.md         # Deploy guide
├── 1_session-install-dependencies/ # stage 1: pip install
├── 2_job-init-database/            # stage 3: warehouse seed
├── 3_job-train-churn-model/        # stage 4: churn training
├── 4_application/                  # stage 5: FastAPI app launcher
├── customer360/                    # Shared Python package (seed, DB, churn, API)
├── data/schema.sql                 # Warehouse DDL
├── scripts/build_frontend.py       # stage 2: React build
└── scripts/init_db.py                # Local dev CLI (same as stage 3 job)
```

### Warehouse domains

| Table | Domain |
| --- | --- |
| `DWH_DIM_CUSTOMERS_UNIQUE` | Master customer dimension (MDM / portal) |
| `DWH_DIM_ALL_POLICY` | Life, health, elementary, pension, and gemel policies |
| `DWH_FCT_FORECLOSURES` / `DWH_FCT_FORECLOSURES_ASSETS` | Legal encumbrances and linked assets |
| `DWH_FCT_POLICY_INVESTMENT_TRACK` | Monthly per-policy accumulation by track |
| `DWH_FCT_INVESTMENT_TRACK` | Regulatory market track performance |
| `DWH_FCT_POLICY_STATUS` | Policy status, coverage, and surrender/savings snapshots |
| `APP_CUSTOMER_CHURN_SCORES` | Churn probability and risk tier per customer ID |
| `APP_CUSTOMER_INTERACTION_EVENTS` | Synthetic reviews, agent questions, and web searches |
| `APP_CUSTOMER_AI_INSIGHTS` | Cached Bedrock (or fallback) customer summaries |

### Churn intelligence

Features are built from warehouse behaviour plus **interaction events** (reviews, agent
questions, product/help searches), normalized with `StandardScaler`, and modeled with
balanced logistic regression. Scores are stored in SQLite for the API and UI. Interaction
aggregates also feed **Amazon Bedrock** insight prompts when configured. Clickable
recommendation drafts (email, SMS, call scripts) are **Bedrock-generated** as well — templates
are not used when Bedrock is available.

```bash
python 3_job-train-churn-model/train_churn.py
```

### Local development

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
python3 scripts/init_db.py
python3 4_application/start-app.py
```

### `__file__` / Workbench interactive runs

`Path(__file__)` is only defined when Python executes a **file** (for example
`python 2_job-init-database/init_database.py`). In an interactive Workbench cell,
pasting lines that use `__file__` raises `NameError`.

Use one of these instead:

```python
# From a session whose working directory is the project root:
%run 2_job-init-database/init_database.py
%run 3_job-train-churn-model/train_churn.py   # after database init
```

```python
import importlib.util
from pathlib import Path

for candidate in (Path.cwd(), *Path.cwd().parents):
    boot = candidate / "bootstrap_entry.py"
    if boot.is_file():
        spec = importlib.util.spec_from_file_location("bootstrap_entry", boot)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.bootstrap(None)
        break

from customer360.paths import default_db_path
from customer360.seed import init_database

init_database(default_db_path(), rebuild=True)
```

On Cloudera AI, `CDSW_PROJECT` is set automatically. If the Git repo lives in a
subfolder (e.g. `midgalpoc/`), bootstrap walks that folder too — you do **not** need
to point `CDSW_PROJECT` at the subfolder, but `%cd midgalpoc` before `%run` is fine.

If install fails with a missing `requirements.txt`, run:

```python
%cd midgalpoc   # folder that contains data/schema.sql
%run 1_session-install-dependencies/install.py
```

Generated databases are gitignored (`data/*.db`).

### Scale to ~5,000 customers

The seed generator uses the same DDS-aligned patterns as the default warehouse (policies,
investments, coverage snapshots, foreclosures, interactions) and scales every table from
that logic:

```bash
python3 scripts/scale_warehouse.py --customers 5000
```

Or set `CUSTOMER360_SEED_CUSTOMERS=5000` before the init job / `python3 -m customer360.seed --customers 5000`, then run `3_job-train-churn-model/train_churn.py` for churn scores.

### API performance (large warehouses)

After seeding, the warehouse precomputes:

- **`APP_CUSTOMER_METRICS`** — per-customer value, policy count, investment tracks (customer list avoids heavy per-row subqueries).
- **`APP_OVERVIEW_COUNTS`** — domain card counts.
- **`APP_PORTFOLIO_ANALYTICS_CACHE`** — portfolio charts/KPIs per segment (seed, churn train, or `scripts/refresh_api_caches.py`). The API serves this JSON on read; cache misses are computed once and stored (write-through).
- **`APP_BOOK_*_TREND`** — materialized book-wide strategic objective series (savings AUM, premium momentum, engagement) for fast chart loads without re-aggregating facts on every request.

Refresh caches on an existing DB without reseeding:

```bash
python3 scripts/refresh_api_caches.py
```

The customer list API enforces **`limit` ≤ 100**; the UI defaults to 50 with 25/50/100 options.

### Frontend without Node on PATH

The repo includes a prebuilt `frontend/dist/`. Restart the application after `git pull` —
you do **not** need `npm` for that.

To rebuild the UI in a standard Python 3.11 CAI session (no system Node):

```python
%run scripts/build_frontend.py
```

The script skips work if `frontend/dist/index.html` already exists. It downloads a
portable Node.js binary into `.tools/` when `npm` is missing (requires outbound HTTPS
to `nodejs.org`).

## Applied AI sentiment reference service

A minimal, self-contained **Applied AI** demo (TF-IDF + logistic regression via
scikit-learn) served through **FastAPI** with a small static web UI. It lives
alongside Customer 360 in this repo and uses its own dependencies
(`applied-ai-sentiment-requirements.txt`).

```
app/              FastAPI app + model training/inference
scripts/train.py  Trains models/sentiment.joblib
static/index.html Demo UI
tests/            pytest unit + API tests
.cursor/          Optional Cloud Agent install/start helpers for this demo
```

```bash
bash .cursor/install.sh   # train model + venv deps for sentiment demo
bash .cursor/start.sh     # http://localhost:8000
```

Manual run: `pip install -r applied-ai-sentiment-requirements.txt`, then
`python -m scripts.train` and `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
